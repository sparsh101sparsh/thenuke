"""Comprehensive Test Suite for Milestone 2: Grilling Protocol & Alignment Engine.

Tests:
- GrillingProfile data model, schema contract, and serialization (PROJECT.md § 4.2).
- Level of Detail, Visual Threshold, and Audience Focus validations.
- Domain priorities sanitization, deduplication, capping, and fallback.
- Visual frame relevance filtering (filter_relevant_visual_frames) across threshold modes.
- Frame classification: code/architecture/slides vs talking-head/generic video frames.
- Interactive interview flow with simulated stdin/output, including image clarification.
- Programmatic builder and convenience runner with corpus topic ingestion.
- Error recovery and boundary resilience.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List
import pytest

from scripts.grilling import (
    DEFAULT_DOMAIN_PRIORITIES,
    LOCKED_TARGET_LANGUAGE,
    VALID_AUDIENCE_FOCUSES,
    VALID_LEVELS_OF_DETAIL,
    VALID_VISUAL_THRESHOLDS,
    GrillingEngine,
    GrillingProfile,
    calculate_frame_relevance_score,
    filter_relevant_visual_frames,
    run_grilling_interview,
    sanitize_domain_priorities,
)
from scripts.ingestion.unified_corpus import ExtractedImage


# ===========================================================================
# 1. GrillingProfile Schema & Contract Conformance (PROJECT.md § 4.2)
# ===========================================================================

class TestGrillingProfileSchema:
    """Verifies profile data model, schema contract, and JSON serialization."""

    def test_default_profile_schema_compliance(self):
        """Verify default profile matches PROJECT.md § 4.2 required schema."""
        profile = GrillingProfile()
        d = profile.to_dict()

        # Schema keys
        expected_keys = {
            "level_of_detail",
            "visual_inclusion_threshold",
            "audience_focus",
            "target_language",
            "domain_priorities",
            "created_at",
        }
        assert set(d.keys()) == expected_keys

        # Default values and invariants
        assert d["level_of_detail"] == "senior_architect"
        assert d["visual_inclusion_threshold"] == "strict_need_based"
        assert d["audience_focus"] == "faang_interview"
        assert d["target_language"] == LOCKED_TARGET_LANGUAGE
        assert isinstance(d["domain_priorities"], list)
        assert len(d["domain_priorities"]) >= 3
        assert "event_loop" in d["domain_priorities"]
        assert isinstance(d["created_at"], str) and len(d["created_at"]) > 0

    def test_valid_levels_of_detail(self):
        """Verify all valid Level of Detail values are accepted."""
        for lod in ["foundations", "resource_parity", "senior_architect"]:
            prof = GrillingProfile(level_of_detail=lod)
            assert prof.level_of_detail == lod

    def test_invalid_level_of_detail_raises_value_error(self):
        """Verify invalid Level of Detail values raise ValueError."""
        for invalid in ["god_mode", "extreme", "level_99", "", "unknown"]:
            with pytest.raises(ValueError, match="Invalid level_of_detail"):
                GrillingProfile(level_of_detail=invalid)

    def test_valid_visual_thresholds(self):
        """Verify all valid Visual Inclusion Threshold values are accepted."""
        for vit in ["strict_need_based", "balanced", "diagram_dense"]:
            prof = GrillingProfile(visual_inclusion_threshold=vit)
            assert prof.visual_inclusion_threshold == vit

    def test_invalid_visual_threshold_raises_value_error(self):
        """Verify invalid Visual Inclusion Threshold values raise ValueError."""
        for invalid in ["infinite_diagrams", "no_text_only_pics", "random", ""]:
            with pytest.raises(ValueError, match="Invalid visual_inclusion_threshold"):
                GrillingProfile(visual_inclusion_threshold=invalid)

    def test_valid_audience_focuses(self):
        """Verify all valid Audience & Focus values are accepted."""
        for focus in ["production_engineering", "faang_interview", "academic_foundations"]:
            prof = GrillingProfile(audience_focus=focus)
            assert prof.audience_focus == focus

    def test_invalid_audience_focus_raises_value_error(self):
        """Verify invalid Audience & Focus values raise ValueError."""
        for invalid in ["casual_hobbyist", "kids_corner", "random", ""]:
            with pytest.raises(ValueError, match="Invalid audience_focus"):
                GrillingProfile(audience_focus=invalid)

    def test_target_language_invariant_locked(self):
        """Target language is locked to roman_hinglish_zero_devanagari even if overridden."""
        prof = GrillingProfile(target_language="anything_else")
        assert prof.target_language == LOCKED_TARGET_LANGUAGE

    def test_json_serialization_round_trip(self, tmp_path):
        """Verify serialization to JSON string and file round-trip integrity."""
        original = GrillingProfile(
            level_of_detail="resource_parity",
            visual_inclusion_threshold="balanced",
            audience_focus="production_engineering",
            domain_priorities=["v8_ignition", "turbofan", "hidden_classes"],
        )
        json_str = original.to_json()
        loaded_from_str = GrillingProfile.from_json(json_str)
        assert loaded_from_str.to_dict() == original.to_dict()

        target_file = tmp_path / "sub" / "grilling_profile.json"
        original.save(target_file)
        assert target_file.exists()

        loaded_from_file = GrillingProfile.load(target_file)
        assert loaded_from_file.to_dict() == original.to_dict()


# ===========================================================================
# 2. Domain Priorities Sanitization & Resilience
# ===========================================================================

class TestDomainPrioritiesSanitization:
    """Verifies sanitization, deduplication, and bounds for domain priorities."""

    def test_sanitizes_special_characters_and_sql_injection(self):
        """Sanitizes quotes, semicolons, script tags, and SQL injection syntax."""
        raw = [' "event_loop"; DROP TABLE users; -- <script> ', "v8`internals`", "async/await#123"]
        cleaned = sanitize_domain_priorities(raw)
        for item in cleaned:
            assert ";" not in item
            assert "<" not in item
            assert ">" not in item
            assert "`" not in item
            assert "#" not in item
        assert any("event_loop" in item for item in cleaned)

    def test_deduplicates_preserving_order(self):
        """Deduplicates items case-insensitively while preserving first occurrence."""
        raw = ["event_loop", "v8_internals", "EVENT_LOOP", "concurrency", "v8_internals"]
        cleaned = sanitize_domain_priorities(raw)
        assert cleaned == ["event_loop", "v8_internals", "concurrency"]

    def test_empty_priorities_fallback_to_defaults(self):
        """Empty or whitespace-only inputs fallback to default priorities."""
        assert sanitize_domain_priorities([]) == DEFAULT_DOMAIN_PRIORITIES
        assert sanitize_domain_priorities(["", "   ", ";;"]) == DEFAULT_DOMAIN_PRIORITIES
        assert sanitize_domain_priorities(None) == DEFAULT_DOMAIN_PRIORITIES

    def test_massive_list_capped(self):
        """Massive list of 100+ items is safely deduplicated and capped to max_count."""
        raw = [f"topic_{i % 30}" for i in range(150)]
        cleaned = sanitize_domain_priorities(raw, max_count=20)
        assert len(cleaned) == 20
        assert len(set(cleaned)) == 20


# ===========================================================================
# 3. Visual Frame Relevance Filter (filter_relevant_visual_frames)
# ===========================================================================

class TestVisualFrameRelevanceFilter:
    """Verifies strict relevance filtering for captured video frames and slides."""

    @pytest.fixture
    def sample_candidate_frames(self) -> List[Dict[str, Any]]:
        return [
            # Frame 1: Technical Architecture Slide (High relevance)
            {
                "path": "frames/slide_01_arch.png",
                "caption": "V8 Memory Architecture: Heap vs Stack",
                "ocr_text": "CALL STACK: Main Thread Execution Frame\nMEMORY HEAP: Young Generation vs Old Generation Nursery\nEvent Loop microtask queue tick",
                "classification": "slide",
                "is_slide": True,
                "has_diagram": True,
            },
            # Frame 2: Code Snippet Frame (High relevance)
            {
                "path": "frames/video_frame_042.png",
                "caption": "Event Loop Microtask Drain Demonstration",
                "ocr_text": "const queue = [];\nfunction drainMicrotasks() {\n  while (queue.length > 0) {\n    const task = queue.shift();\n    task();\n  }\n}\nexport default drainMicrotasks;",
                "classification": "code",
                "has_code": True,
            },
            # Frame 3: Talking Head / Presenter Webcam (Irrelevant -> Must be filtered out)
            {
                "path": "frames/talking_head_01.png",
                "caption": "Instructor introducing the chapter",
                "ocr_text": "Follow @instructor on Twitter",
                "classification": "talking_head",
                "is_slide": False,
            },
            # Frame 4: Generic Low-Content Title Card (Low relevance)
            {
                "path": "frames/title_card.png",
                "caption": "Chapter 2 Overview",
                "ocr_text": "Chapter 2",
                "classification": "generic",
            },
            # Frame 5: Informative bullet slide (Moderate relevance)
            {
                "path": "frames/slide_05_bullets.png",
                "caption": "Invariants of Microtask Execution",
                "ocr_text": "Key Invariants:\n1. Promise callbacks resolve in microtask queue\n2. Microtask queue drains completely before macrotask\n3. MutationObserver runs in microtask tick",
                "classification": "slide",
                "is_slide": True,
            },
        ]

    def test_strict_need_based_mode_filters_talking_head_and_generic(self, sample_candidate_frames):
        """strict_need_based mode includes only high-relevance architecture & code frames."""
        filtered = filter_relevant_visual_frames(
            sample_candidate_frames,
            threshold_mode="strict_need_based",
        )
        paths = [f["path"] for f in filtered]

        # Architecture diagram and code snippet must be retained
        assert "frames/slide_01_arch.png" in paths
        assert "frames/video_frame_042.png" in paths

        # Talking head and generic title card must be discarded
        assert "frames/talking_head_01.png" not in paths
        assert "frames/title_card.png" not in paths

    def test_balanced_mode_inclusion(self, sample_candidate_frames):
        """balanced mode retains architecture, code, and informative bullet slides."""
        filtered = filter_relevant_visual_frames(
            sample_candidate_frames,
            threshold_mode="balanced",
        )
        paths = [f["path"] for f in filtered]

        assert "frames/slide_01_arch.png" in paths
        assert "frames/video_frame_042.png" in paths
        assert "frames/slide_05_bullets.png" in paths
        # Still drops talking head
        assert "frames/talking_head_01.png" not in paths

    def test_diagram_dense_mode(self, sample_candidate_frames):
        """diagram_dense retains all informative frames but still excludes talking heads."""
        filtered = filter_relevant_visual_frames(
            sample_candidate_frames,
            threshold_mode="diagram_dense",
        )
        paths = [f["path"] for f in filtered]

        assert "frames/slide_01_arch.png" in paths
        assert "frames/video_frame_042.png" in paths
        assert "frames/slide_05_bullets.png" in paths
        assert "frames/talking_head_01.png" not in paths

    def test_topic_relevance_boost(self):
        """Frames mentioning the query topic get a relevance score boost."""
        frame_generic = {
            "path": "frames/generic.png",
            "caption": "Performance tips",
            "ocr_text": "Tip: optimize your rendering tree and css selectors",
            "classification": "slide",
        }
        frame_topic_specific = {
            "path": "frames/event_loop.png",
            "caption": "Event Loop Internals",
            "ocr_text": "Event Loop microtask queue tick and macrotask execution invariants",
            "classification": "slide",
        }

        score_gen, _ = calculate_frame_relevance_score(frame_generic, topic="event loop")
        score_spec, _ = calculate_frame_relevance_score(frame_topic_specific, topic="event loop")

        assert score_spec > score_gen

    def test_extracted_image_dataclass_support(self):
        """Filter supports ExtractedImage instances from unified corpus."""
        images = [
            ExtractedImage(
                path="assets/img1.png",
                caption="Architecture Flow",
                ocr_text="CALL STACK: frame 1 -> frame 2 -> heap allocation pointer diagram",
            ),
            ExtractedImage(
                path="assets/img2_face.png",
                caption="Speaker face talking head",
                ocr_text="Subscribe now",
            ),
        ]

        filtered = filter_relevant_visual_frames(images, threshold_mode="strict_need_based")
        assert len(filtered) == 1
        assert isinstance(filtered[0], ExtractedImage)
        assert filtered[0].path == "assets/img1.png"

    def test_empty_candidates_returns_empty_list(self):
        """Empty candidate frame list returns empty list safely."""
        assert filter_relevant_visual_frames([]) == []

    def test_invalid_threshold_mode_raises(self, sample_candidate_frames):
        """Invalid threshold mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid threshold_mode"):
            filter_relevant_visual_frames(sample_candidate_frames, threshold_mode="ultra_high")


# ===========================================================================
# 4. Interactive Interview Flow & Image Clarification
# ===========================================================================

class TestInteractiveGrillingInterview:
    """Verifies interactive questionnaire prompts, input parsing, and clarification."""

    def test_interactive_default_flow_with_simulated_inputs(self):
        """Pressing Enter for all options chooses defaults."""
        inputs = iter(["", "", "", ""])  # LOD, VIT, Focus, Priorities
        printed_lines: List[str] = []

        engine = GrillingEngine(
            input_fn=lambda prompt: next(inputs),
            print_fn=lambda msg: printed_lines.append(str(msg)),
        )

        profile = engine.conduct_interview(non_interactive=False)
        assert profile.level_of_detail == "senior_architect"
        assert profile.visual_inclusion_threshold == "strict_need_based"
        assert profile.audience_focus == "faang_interview"
        assert profile.domain_priorities == DEFAULT_DOMAIN_PRIORITIES

        # Assert mandatory image clarification message was displayed
        output_text = "\n".join(printed_lines)
        assert "CLARIFICATION: In 'thenuke', 'images' specifically refers to captured" in output_text
        assert "video frames and presentation slides" in output_text

    def test_interactive_explicit_choice_selections(self):
        """Entering numeric options [1, 2, 3] selects corresponding options."""
        # 1 -> foundations, 2 -> balanced, 1 -> production_engineering, custom topics
        inputs = iter(["1", "2", "1", "event_loop, v8_internals, memory_profiling"])

        engine = GrillingEngine(
            input_fn=lambda prompt: next(inputs),
            print_fn=lambda msg: None,
        )

        profile = engine.conduct_interview(non_interactive=False)
        assert profile.level_of_detail == "foundations"
        assert profile.visual_inclusion_threshold == "balanced"
        assert profile.audience_focus == "production_engineering"
        assert profile.domain_priorities == ["event_loop", "v8_internals", "memory_profiling"]

    def test_interactive_string_inputs_normalized(self):
        """Textual answers like 'parity', 'diagram_dense', 'academic' normalized properly."""
        inputs = iter(["parity", "diagram_dense", "academic", ""])

        engine = GrillingEngine(
            input_fn=lambda prompt: next(inputs),
            print_fn=lambda msg: None,
        )

        profile = engine.conduct_interview(non_interactive=False)
        assert profile.level_of_detail == "resource_parity"
        assert profile.visual_inclusion_threshold == "diagram_dense"
        assert profile.audience_focus == "academic_foundations"

    def test_invalid_input_repairs_after_retry(self):
        """Engine prompts again when given invalid input."""
        inputs = iter(["invalid_choice", "3", "bad_vit", "1", "2", ""])

        engine = GrillingEngine(
            input_fn=lambda prompt: next(inputs),
            print_fn=lambda msg: None,
        )

        profile = engine.conduct_interview(non_interactive=False)
        assert profile.level_of_detail == "senior_architect"
        assert profile.visual_inclusion_threshold == "strict_need_based"
        assert profile.audience_focus == "faang_interview"

    def test_eof_handling_falls_back_to_defaults(self):
        """EOFError during input triggers graceful default fallback."""
        def eof_input(prompt: str):
            raise EOFError("simulated eof")

        engine = GrillingEngine(
            input_fn=eof_input,
            print_fn=lambda msg: None,
        )

        profile = engine.conduct_interview(non_interactive=False)
        assert profile.level_of_detail == "senior_architect"
        assert profile.visual_inclusion_threshold == "strict_need_based"
        assert profile.audience_focus == "faang_interview"


# ===========================================================================
# 5. Programmatic Builder & Convenience Runner
# ===========================================================================

class TestProgrammaticGrillingBuilder:
    """Verifies non-interactive execution and corpus topic integration."""

    def test_build_profile_programmatically(self):
        """build_profile constructs custom profile cleanly."""
        engine = GrillingEngine()
        profile = engine.build_profile(
            level_of_detail="foundations",
            visual_inclusion_threshold="diagram_dense",
            audience_focus="academic_foundations",
            domain_priorities=["closures", "lexical_scope", "prototypes"],
        )
        assert profile.level_of_detail == "foundations"
        assert profile.visual_inclusion_threshold == "diagram_dense"
        assert profile.audience_focus == "academic_foundations"
        assert profile.domain_priorities == ["closures", "lexical_scope", "prototypes"]

    def test_run_grilling_interview_non_interactive_with_corpus_file(self, tmp_path):
        """run_grilling_interview reads corpus topics and writes output file."""
        corpus_data = {
            "corpus_id": "test_corpus_42",
            "aggregated_topics": ["turbofan_jit", "hidden_classes", "inline_caches"],
            "sources": [],
        }
        corpus_file = tmp_path / "nuke_ingestion_corpus.json"
        corpus_file.write_text(json.dumps(corpus_data), encoding="utf-8")

        out_profile = tmp_path / "grilling_profile.json"

        profile = run_grilling_interview(
            corpus=corpus_file,
            output_path=out_profile,
            interactive=False,
            level_of_detail="senior_architect",
        )

        assert out_profile.exists()
        loaded = json.loads(out_profile.read_text(encoding="utf-8"))
        assert loaded["level_of_detail"] == "senior_architect"
        assert loaded["domain_priorities"] == ["turbofan_jit", "hidden_classes", "inline_caches"]

    def test_run_grilling_interview_with_overrides(self, tmp_path):
        """run_grilling_interview respects explicit argument overrides."""
        out_profile = tmp_path / "profile.json"
        profile = run_grilling_interview(
            output_path=out_profile,
            interactive=False,
            level_of_detail="resource_parity",
            visual_inclusion_threshold="balanced",
            audience_focus="production_engineering",
            domain_priorities=["event_loop", "microtasks", "macrotasks"],
        )
        assert profile.level_of_detail == "resource_parity"
        assert profile.visual_inclusion_threshold == "balanced"
        assert profile.audience_focus == "production_engineering"
        assert profile.domain_priorities == ["event_loop", "microtasks", "macrotasks"]


# ===========================================================================
# 6. Error Recovery & Boundary Cases
# ===========================================================================

class TestGrillingErrorRecovery:
    """Verifies edge case handling and error recovery."""

    def test_load_nonexistent_profile_raises(self, tmp_path):
        """Attempting to load a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            GrillingProfile.load(tmp_path / "nonexistent.json")

    def test_save_creates_parent_directories_automatically(self, tmp_path):
        """Saving to a deep nested path creates parent directories automatically."""
        deep_path = tmp_path / "nested" / "deeply" / "grilling_profile.json"
        prof = GrillingProfile()
        saved = prof.save(deep_path)
        assert saved.exists()
        assert deep_path.exists()

    def test_load_corrupted_json_raises(self, tmp_path):
        """Loading corrupted JSON raises json.JSONDecodeError."""
        bad_file = tmp_path / "corrupt.json"
        bad_file.write_text("{ not valid json !!! }", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            GrillingProfile.load(bad_file)


# ===========================================================================
# 7. Remediation Verification: Empirical Vulnerability Fixes
# ===========================================================================

class TestRemediatedGrillingVulnerabilities:
    """Verifies remediation of the 4 empirical vulnerabilities identified by Challenger."""

    def test_interface_introduction_not_flagged_as_talking_head(self):
        """Word-bounded matching ensures 'interface' and 'introduction' never trigger talking-head penalty."""
        # 1. Interface diagram with 'interface' in caption and path
        iface_diagram = {
            "path": "slides/interface_hierarchy.png",
            "caption": "DOM Interface and EventTarget Hierarchy",
            "ocr_text": "EventTarget -> Node -> Element -> HTMLElement",
            "classification": "diagram",
            "has_diagram": True,
        }
        score, details = calculate_frame_relevance_score(iface_diagram)
        assert details["is_talking_head"] is False
        assert details["diagram_score"] >= 0.45
        assert score >= 0.55
        assert len(filter_relevant_visual_frames([iface_diagram], threshold_mode="strict_need_based")) == 1

        # 2. Introduction architecture frame with 'introduction' in caption
        intro_diagram = {
            "path": "slides/intro_arch.png",
            "caption": "Introduction and Introspection Architecture",
            "ocr_text": "CALL STACK -> EVENT LOOP TICK -> MICROTASK QUEUE",
            "classification": "architecture",
            "has_diagram": True,
        }
        intro_score, intro_details = calculate_frame_relevance_score(intro_diagram)
        assert intro_details["is_talking_head"] is False
        assert intro_score >= 0.55
        assert len(filter_relevant_visual_frames([intro_diagram], threshold_mode="strict_need_based")) == 1

        # 3. Genuine webcam talking head IS still detected and penalized
        webcam_frame = {
            "path": "frames/speaker_face.png",
            "caption": "Speaker face talking head presenter",
            "ocr_text": "Subscribe to channel",
            "classification": "talking_head",
        }
        wb_score, wb_details = calculate_frame_relevance_score(webcam_frame)
        assert wb_details["is_talking_head"] is True
        assert wb_score == 0.0
        assert len(filter_relevant_visual_frames([webcam_frame], threshold_mode="strict_need_based")) == 0

    def test_concise_architecture_diagram_qualifies_strict_need_based(self):
        """Concise diagrams (has_diagram=True, OCR >= 15 chars) qualify under strict_need_based."""
        concise_diagram = {
            "path": "extracted/pure_diagram.png",
            "caption": "Architecture flowchart",
            "ocr_text": "Event Loop and Microtask Queue tick",
            "has_diagram": True,
        }
        score, details = calculate_frame_relevance_score(concise_diagram)
        assert details["diagram_score"] >= 0.45
        assert score >= 0.55
        filtered_strict = filter_relevant_visual_frames([concise_diagram], threshold_mode="strict_need_based")
        assert len(filtered_strict) == 1
        assert filtered_strict[0]["path"] == "extracted/pure_diagram.png"

        # Verify plain bullet slide without diagram does NOT get full diagram score
        prose_bullet_slide = {
            "path": "slides/prose_notes.png",
            "caption": "Notes on Call Stack and Microtask Queue",
            "ocr_text": (
                "The Call Stack executes synchronous frames one by one. "
                "Once the stack is clear, the Event Loop checks the Microtask Queue. "
                "Promises and MutationObservers drain here completely."
            ),
            "classification": "slide",
            "is_slide": True,
            "has_diagram": False,
        }
        bullet_score, bullet_details = calculate_frame_relevance_score(prose_bullet_slide)
        # Diagram score on prose slide must be capped (< 0.10)
        assert bullet_details["diagram_score"] < 0.10
        # Total score must not falsely cross strict threshold (0.55)
        assert bullet_score < 0.55
        assert len(filter_relevant_visual_frames([prose_bullet_slide], threshold_mode="strict_need_based")) == 0
        # But passes balanced mode
        assert len(filter_relevant_visual_frames([prose_bullet_slide], threshold_mode="balanced")) == 1

    def test_topic_matching_normalizes_underscores(self):
        """Underscore topic strings (event_loop, v8_internals) match natural text in OCR."""
        frame = {
            "path": "frames/v8_slide.png",
            "caption": "V8 Runtime Architecture",
            "ocr_text": "Call Stack and Event Loop Microtask Queue in V8 Engine Runtime",
            "classification": "slide",
        }
        # Both underscore and space versions must award the topic boost
        _, details_underscore = calculate_frame_relevance_score(frame, topic="event_loop")
        _, details_space = calculate_frame_relevance_score(frame, topic="event loop")

        assert details_underscore["topic_boost"] > 0.0
        assert details_space["topic_boost"] > 0.0
        assert details_underscore["topic_boost"] == details_space["topic_boost"]

    def test_safe_entropy_handling(self):
        """calculate_frame_relevance_score handles non-float entropy safely without exceptions."""
        test_payloads = [
            {"path": "f1.png", "ocr_text": "Code snippet", "entropy": "high"},
            {"path": "f2.png", "ocr_text": "Code snippet", "entropy": "invalid_entropy_string"},
            {"path": "f3.png", "ocr_text": "Code snippet", "entropy": ""},
            {"path": "f4.png", "ocr_text": "Code snippet", "entropy": None},
            {"path": "f5.png", "ocr_text": "Code snippet", "entropy": [1, 2, 3]},
            {"path": "f6.png", "ocr_text": "Code snippet", "entropy": 0.85},
            {"path": "f7.png", "ocr_text": "Code snippet", "entropy": "0.75"},
        ]

        for payload in test_payloads:
            score, details = calculate_frame_relevance_score(payload)
            assert isinstance(score, float)
            assert isinstance(details, dict)
            assert 0.0 <= score <= 1.0
