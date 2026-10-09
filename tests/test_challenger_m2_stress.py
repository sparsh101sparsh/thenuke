"""Empirical Adversarial Stress & Verification Test Suite for Milestone 2.

Author: Milestone 2 Empirical Challenger (teamwork_preview_challenger)
Role: critic, specialist

Rigorous empirical testing and vulnerability verification for:
1. `filter_relevant_visual_frames` & `calculate_frame_relevance_score`:
   - High-density whiteboard/architecture frames vs zero-text talking-head frames
   - Talking-head frames with spoken code/keywords vs genuine diagram slides
   - OCR noise, non-standard text, leetspeak, and massive OCR payloads (100k chars)
   - Calibrated threshold cuts across strict_need_based (0.55), balanced (0.30), diagram_dense (0.15)
   - Vulnerability: False-positive talking head misclassification caused by unanchored substring matching
     ("face" in "interface", "intro" in "introduction", "intro" in "introspection")
   - Vulnerability: Rejection of concise architecture diagrams (< 50 chars OCR) under strict_need_based (0.55)
   - Edge Case: Tokenization difference for underscore topics ('event_loop' vs 'event loop')
   - Resilience: Malformed candidate frame objects (None, dict with None values, missing keys, generic classes)
2. `GrillingProfile` schema validation & persistence:
   - Locked target language invariant (`roman_hinglish_zero_devanagari`)
   - Schema conformance against PROJECT.md § 4.2
   - Malformed/corrupted JSON, non-dict payloads, missing fields
   - Enum validation & normalization for LOD, VIT, and Audience Focus
3. `sanitize_domain_priorities`:
   - Shell, SQL, and HTML/XSS injection payloads
   - Massive list capping (1,000+ items capped to 20)
   - Heterogeneous types, case-insensitive deduplication, and fallback mechanisms
   - Edge Case: Character-level iteration when string is passed instead of list of strings
4. `GrillingEngine` & `run_grilling_interview`:
   - Mandatory image clarification message verification
   - Interactive retry on malformed inputs, EOF recovery, corpus error handling
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest

from scripts.grilling import (
    DEFAULT_DOMAIN_PRIORITIES,
    FOCUS_MAPPINGS,
    LOCKED_TARGET_LANGUAGE,
    LOD_MAPPINGS,
    VALID_AUDIENCE_FOCUSES,
    VALID_LEVELS_OF_DETAIL,
    VALID_VISUAL_THRESHOLDS,
    VIT_MAPPINGS,
    GrillingEngine,
    GrillingProfile,
    calculate_frame_relevance_score,
    filter_relevant_visual_frames,
    run_grilling_interview,
    sanitize_domain_priorities,
)
from scripts.ingestion.unified_corpus import ExtractedImage


# ===========================================================================
# 1. Adversarial Visual Frame Relevance Filtering
# ===========================================================================

class TestAdversarialVisualFrameFiltering:
    """Stress tests visual frame relevance heuristics and threshold modes."""

    def test_talking_head_zero_text_is_strictly_filtered(self):
        """Zero-text talking head webcam frames are rejected in all threshold modes."""
        frame = {
            "path": "frames/webcam_presenter_001.png",
            "caption": "Presenter talking to camera",
            "ocr_text": "",
            "classification": "talking_head",
            "is_slide": False,
        }
        score, details = calculate_frame_relevance_score(frame)
        assert details["is_talking_head"] is True
        assert score == 0.0

        for mode in ["strict_need_based", "balanced", "diagram_dense"]:
            filtered = filter_relevant_visual_frames([frame], threshold_mode=mode)
            assert len(filtered) == 0, f"Failed for mode {mode}: zero-text talking head was not rejected"

    def test_talking_head_with_incidental_spoken_keywords_rejected(self):
        """Talking head frames where speaker mentions technical keywords in subtitles/OCR are rejected."""
        frame = {
            "path": "frames/talking_head_with_captions.png",
            "caption": "Host speaking to audience",
            "ocr_text": "Hey guys! Welcome to JavaScript tutorial. Let us talk about function, const, return, and async await promises.",
            "classification": "talking_head",
            "is_slide": False,
        }
        score, details = calculate_frame_relevance_score(frame)
        assert details["is_talking_head"] is True
        # Severe talking head penalty (-0.75) suppresses score
        assert score < 0.30

        # Must be rejected in strict_need_based and balanced
        assert len(filter_relevant_visual_frames([frame], threshold_mode="strict_need_based")) == 0
        assert len(filter_relevant_visual_frames([frame], threshold_mode="balanced")) == 0

    def test_high_density_whiteboard_architecture_is_retained(self):
        """Dense architectural diagrams on whiteboards score highly and pass all modes."""
        whiteboard_frame = {
            "path": "frames/whiteboard_event_loop.png",
            "caption": "Detailed whiteboard architecture flowchart",
            "ocr_text": (
                "V8 Engine Architecture: Call Stack execution frame -> "
                "Event Loop microtask queue tick -> Macrotask pipeline. "
                "Memory Heap young generation nursery & old generation pointers."
            ),
            "classification": "whiteboard",
            "has_diagram": True,
            "is_slide": False,
        }
        score, details = calculate_frame_relevance_score(whiteboard_frame)
        assert details["is_talking_head"] is False
        assert details["diagram_score"] >= 0.35
        assert score >= 0.60

        for mode in ["strict_need_based", "balanced", "diagram_dense"]:
            filtered = filter_relevant_visual_frames([whiteboard_frame], threshold_mode=mode)
            assert len(filtered) == 1
            assert filtered[0]["path"] == "frames/whiteboard_event_loop.png"

    def test_high_density_code_slide_is_retained(self):
        """Dense code slides with syntax structures score highly and pass all modes."""
        code_slide = {
            "path": "frames/slide_code_es2024.png",
            "caption": "ES2024 Object.groupBy and Promise.withResolvers Implementation",
            "ocr_text": (
                "const { promise, resolve, reject } = Promise.withResolvers();\n"
                "class TaskQueue {\n"
                "  #items = [];\n"
                "  async process() {\n"
                "    const grouped = Object.groupBy(this.#items, item => item.priority);\n"
                "    return grouped;\n"
                "  }\n"
                "}\n"
                "export default TaskQueue;"
            ),
            "classification": "slide",
            "is_slide": True,
            "has_code": True,
        }
        score, details = calculate_frame_relevance_score(code_slide)
        assert details["is_talking_head"] is False
        assert details["code_score"] >= 0.30
        assert score >= 0.60

        for mode in ["strict_need_based", "balanced", "diagram_dense"]:
            filtered = filter_relevant_visual_frames([code_slide], threshold_mode=mode)
            assert len(filtered) == 1

    def test_ambiguous_slides_differentiated_across_threshold_cuts(self):
        """Verifies clear separation of ambiguous frames across threshold cuts."""
        # 1. Low-density title card (no pedagogical visual value)
        title_card = {
            "path": "frames/title_overview.png",
            "caption": "Getting Started Overview",
            "ocr_text": "Section 1: Getting Started",
            "classification": "slide",
            "is_slide": True,
        }
        # 2. Informative bullet slide (moderate textual value, no architecture/code diagrams)
        bullet_slide = {
            "path": "frames/bullet_summary.png",
            "caption": "Execution Summary",
            "ocr_text": (
                "Key Rules:\n"
                "1. Synchronous rules apply in each phase.\n"
                "2. Tasks run immediately after steps clear.\n"
                "3. Handlers yield to the browser rendering frame."
            ),
            "classification": "slide",
            "is_slide": True,
        }
        # 3. Dense architecture diagram slide
        arch_slide = {
            "path": "frames/arch_v8.png",
            "caption": "V8 Runtime Architecture",
            "ocr_text": "Call Stack -> Event Loop -> Heap allocation pointers graph with GC pipeline.",
            "classification": "slide",
            "is_slide": True,
            "has_diagram": True,
        }

        frames = [title_card, bullet_slide, arch_slide]

        # strict_need_based (cutoff 0.55): ONLY architecture diagram retained
        strict_result = filter_relevant_visual_frames(frames, threshold_mode="strict_need_based")
        strict_paths = [f["path"] for f in strict_result]
        assert strict_paths == ["frames/arch_v8.png"]

        # balanced (cutoff 0.30): architecture diagram + informative bullet slide retained, title card dropped
        balanced_result = filter_relevant_visual_frames(frames, threshold_mode="balanced")
        balanced_paths = [f["path"] for f in balanced_result]
        assert "frames/arch_v8.png" in balanced_paths
        assert "frames/bullet_summary.png" in balanced_paths
        assert "frames/title_overview.png" not in balanced_paths

        # diagram_dense (cutoff 0.15): all 3 slides retained
        dense_result = filter_relevant_visual_frames(frames, threshold_mode="diagram_dense")
        dense_paths = [f["path"] for f in dense_result]
        assert len(dense_paths) == 3

    def test_talking_head_substring_false_positive_remediated(self):
        """Verifies: unanchored 'face' and 'intro' substrings do NOT trigger false-positive talking_head flags.

        Vulnerability Remediation:
        1. 'face' in TALKING_HEAD_INDICATORS does NOT match inside technical words like 'interface'
           (e.g., 'DOM Interface Hierarchy', 'TypeScript Interface Diagram').
        2. 'intro' in TALKING_HEAD_INDICATORS does NOT match inside words like 'introduction' or 'introspection'
           (e.g., 'V8 Object Introspection Diagram').
        3. 'face' in path.lower() is word-bounded so paths containing 'interface' do NOT get penalty.
        """
        # Case A: Interface diagram
        interface_frame = {
            "path": "slides/dom_hierarchy.png",
            "caption": "DOM Interface and EventTarget Hierarchy",
            "ocr_text": "EventTarget -> Node -> Element -> HTMLElement",
            "classification": "diagram",
            "has_diagram": True,
        }
        score_iface, details_iface = calculate_frame_relevance_score(interface_frame)
        assert details_iface["is_talking_head"] is False
        assert score_iface >= 0.50
        assert len(filter_relevant_visual_frames([interface_frame], threshold_mode="strict_need_based")) == 1

        # Case B: Introduction architecture diagram
        intro_frame = {
            "path": "slides/arch_01.png",
            "caption": "Introduction to Event Loop and Call Stack Architecture",
            "ocr_text": "CALL STACK -> EVENT LOOP TICK -> MICROTASK QUEUE",
            "classification": "slide",
            "is_slide": True,
            "has_diagram": True,
        }
        score_intro, details_intro = calculate_frame_relevance_score(intro_frame)
        assert details_intro["is_talking_head"] is False
        assert score_intro >= 0.50
        assert len(filter_relevant_visual_frames([intro_frame], threshold_mode="strict_need_based")) == 1

        # Case C: Filename containing 'interface'
        path_iface_frame = {
            "path": "extracted/interface_hierarchy.png",
            "caption": "Class Hierarchy Architecture",
            "ocr_text": "CALL STACK -> HEAP GRAPH -> OBJECT PROTOTYPE CHAIN",
            "classification": "diagram",
            "has_diagram": True,
        }
        score_path, details_path = calculate_frame_relevance_score(path_iface_frame)
        assert details_path["is_talking_head"] is False
        assert score_path >= 0.50
        assert len(filter_relevant_visual_frames([path_iface_frame], threshold_mode="strict_need_based")) == 1

    def test_concise_diagram_without_slide_flag_qualifies_strict(self):
        """Verifies: concise diagrams (<50 chars OCR) with has_diagram=True qualify under strict cutoff 0.55."""
        concise_diagram = {
            "path": "extracted/pure_diagram.png",
            "caption": "Architecture flowchart",
            "ocr_text": "Event Loop and Microtask Queue tick",
            "has_diagram": True,
        }
        score, details = calculate_frame_relevance_score(concise_diagram)
        assert score >= 0.55  # 0.12 (ocr) + 0.45 (diagram) >= 0.55
        # Safely included across all threshold modes
        assert len(filter_relevant_visual_frames([concise_diagram], threshold_mode="strict_need_based")) == 1
        assert len(filter_relevant_visual_frames([concise_diagram], threshold_mode="balanced")) == 1
        assert len(filter_relevant_visual_frames([concise_diagram], threshold_mode="diagram_dense")) == 1

    def test_topic_boost_tokenization_underscore_matches_space(self):
        """Verifies: underscore topics ('event_loop') tokenize to match natural space OCR text ('event loop')."""
        frame = {
            "path": "frames/slide.png",
            "caption": "Event loop diagram",
            "ocr_text": "Event Loop Microtask Queue Architecture Diagram",
            "classification": "slide",
        }
        _, details_underscore = calculate_frame_relevance_score(frame, topic="event_loop")
        _, details_space = calculate_frame_relevance_score(frame, topic="event loop")

        assert details_underscore["topic_boost"] > 0.0
        assert details_space["topic_boost"] > 0.0
        assert details_underscore["topic_boost"] == details_space["topic_boost"]

    def test_noisy_ocr_with_code_syntax_fallback(self):
        """Code slide with noisy OCR (non-alphanumeric keywords) still detects code markers."""
        noisy_frame = {
            "path": "frames/noisy_code.png",
            "caption": "Code snapshot with noisy OCR",
            "ocr_text": "c0nst x = 42; // n0isy 0cr\n{\n  => val => ({ res: val * 2 });\n}\n",
            "classification": "unknown",
        }
        score, details = calculate_frame_relevance_score(noisy_frame)
        # Arrow function '=>' and brace pair '{' '}' trigger syntax fallback
        assert details["code_score"] >= 0.25
        assert score >= 0.30

    def test_massive_ocr_text_performance_and_no_crash(self):
        """Massive OCR text (100k characters) computes in linear time without regex hang/ReDoS."""
        massive_text = ("function testAsyncWorker() { const x = 1; return x; }\n" * 1500)[:100_000]
        frame = {
            "path": "frames/massive_doc.png",
            "caption": "Massive document frame",
            "ocr_text": massive_text,
            "classification": "code",
        }
        start_t = time.perf_counter()
        score, details = calculate_frame_relevance_score(frame)
        elapsed = time.perf_counter() - start_t

        assert elapsed < 0.5, f"Scoring took too long: {elapsed:.3f}s (possible ReDoS)"
        assert score >= 0.60
        assert details["ocr_score"] == 0.35

    def test_malformed_frame_objects_handled_gracefully(self):
        """Malformed frame representations (None, non-dict, missing fields) do not crash."""
        malformed_candidates = [
            None,
            {},
            {"path": None, "ocr_text": None, "caption": None},
            {"path": 12345, "ocr_text": False},
            "not a frame object",
        ]
        # Should execute safely without raising unhandled exceptions
        filtered = filter_relevant_visual_frames(malformed_candidates, threshold_mode="strict_need_based")
        assert isinstance(filtered, list)
        # All malformed empty/invalid items should be filtered out
        assert len(filtered) == 0

    def test_extracted_image_dataclass_roundtrip_filtering(self):
        """ExtractedImage objects from ingestion are processed and retain type."""
        img1 = ExtractedImage(
            path="extracted/img1.png",
            caption="Event Loop Architecture Diagram",
            ocr_text="CALL STACK, MICROTASK QUEUE, MACROTASK TICK, EVENT LOOP ENGINE V8 RUNTIME",
        )
        img2 = ExtractedImage(
            path="extracted/talking_head_02.png",
            caption="Speaker portrait webcam",
            ocr_text="",
        )
        filtered = filter_relevant_visual_frames([img1, img2], threshold_mode="strict_need_based")
        assert len(filtered) == 1
        assert isinstance(filtered[0], ExtractedImage)
        assert filtered[0].path == "extracted/img1.png"

    def test_threshold_mode_aliases_and_case_insensitivity(self):
        """VIT_MAPPINGS aliases ('strict', 'need_based', 'balanced', 'dense', 'yes') normalize properly."""
        frame = {
            "path": "frames/sample.png",
            "caption": "Architecture frame",
            "ocr_text": "CALL STACK and EVENT LOOP microtask queue tick in V8 engine runtime",
            "has_diagram": True,
        }
        for alias in ["strict", "STRICT_NEED_BASED", "need_based", "yes", "Y"]:
            res = filter_relevant_visual_frames([frame], threshold_mode=alias)
            assert len(res) == 1

        for alias in ["balanced", "BALANCED", "2"]:
            res = filter_relevant_visual_frames([frame], threshold_mode=alias)
            assert len(res) == 1

        for alias in ["dense", "diagram_dense", "3"]:
            res = filter_relevant_visual_frames([frame], threshold_mode=alias)
            assert len(res) == 1

    def test_invalid_threshold_mode_raises_value_error(self):
        """Invalid threshold mode raises ValueError with helpful message."""
        with pytest.raises(ValueError, match="Invalid threshold_mode"):
            filter_relevant_visual_frames([], threshold_mode="infinite_images")


# ===========================================================================
# 2. Adversarial GrillingProfile Schema & Invariant Validation
# ===========================================================================

class TestAdversarialGrillingProfileSchema:
    """Stress tests profile data model, schema contract, and invariant locking."""

    def test_target_language_invariant_immutable_under_adversarial_overrides(self):
        """Target language CANNOT be set to anything other than roman_hinglish_zero_devanagari."""
        adversarial_attempts = [
            "english",
            "hindi_devanagari",
            "devanagari",
            "spanish",
            "",
            None,
            "Hinglish",
        ]
        for attempt in adversarial_attempts:
            p = GrillingProfile(target_language=attempt)
            assert p.target_language == LOCKED_TARGET_LANGUAGE
            assert p.to_dict()["target_language"] == LOCKED_TARGET_LANGUAGE

            # Also verify via from_dict
            p_dict = GrillingProfile.from_dict({"target_language": attempt})
            assert p_dict.target_language == LOCKED_TARGET_LANGUAGE

    def test_strict_compliance_with_project_md_schema(self):
        """Generated dictionary strictly matches the schema in PROJECT.md § 4.2."""
        p = GrillingProfile()
        d = p.to_dict()

        expected_schema = {
            "level_of_detail": str,
            "visual_inclusion_threshold": str,
            "audience_focus": str,
            "target_language": str,
            "domain_priorities": list,
            "created_at": str,
        }
        for key, expected_type in expected_schema.items():
            assert key in d, f"Missing key {key} from profile schema"
            assert isinstance(d[key], expected_type), f"Key {key} has type {type(d[key])}, expected {expected_type}"

        assert d["level_of_detail"] in VALID_LEVELS_OF_DETAIL
        assert d["visual_inclusion_threshold"] in VALID_VISUAL_THRESHOLDS
        assert d["audience_focus"] in VALID_AUDIENCE_FOCUSES
        assert d["target_language"] == LOCKED_TARGET_LANGUAGE

    def test_empty_dict_from_dict_falls_back_to_valid_defaults(self):
        """from_dict({}) populates all default fields and produces valid profile."""
        p = GrillingProfile.from_dict({})
        assert p.level_of_detail == "senior_architect"
        assert p.visual_inclusion_threshold == "strict_need_based"
        assert p.audience_focus == "faang_interview"
        assert p.target_language == LOCKED_TARGET_LANGUAGE
        assert p.domain_priorities == DEFAULT_DOMAIN_PRIORITIES
        assert len(p.created_at) > 0

    def test_invalid_level_of_detail_rejected(self):
        """Invalid level_of_detail strings raise ValueError."""
        for invalid in ["god_mode", "ultra", "extreme", "none", "100"]:
            with pytest.raises(ValueError, match="Invalid level_of_detail"):
                GrillingProfile(level_of_detail=invalid)

    def test_invalid_visual_threshold_rejected(self):
        """Invalid visual_inclusion_threshold strings raise ValueError."""
        for invalid in ["unlimited", "maximum", "zero_visuals", "bad_threshold"]:
            with pytest.raises(ValueError, match="Invalid visual_inclusion_threshold"):
                GrillingProfile(visual_inclusion_threshold=invalid)

    def test_invalid_audience_focus_rejected(self):
        """Invalid audience_focus strings raise ValueError."""
        for invalid in ["general_public", "children", "casual", "bad_focus"]:
            with pytest.raises(ValueError, match="Invalid audience_focus"):
                GrillingProfile(audience_focus=invalid)

    def test_valid_aliases_normalized_correctly(self):
        """Valid aliases ('beginner', 'parity', 'architect') normalize to canonical enum values."""
        assert GrillingProfile(level_of_detail="beginner").level_of_detail == "foundations"
        assert GrillingProfile(level_of_detail="parity").level_of_detail == "resource_parity"
        assert GrillingProfile(level_of_detail="architect").level_of_detail == "senior_architect"
        assert GrillingProfile(level_of_detail="1").level_of_detail == "foundations"
        assert GrillingProfile(level_of_detail="2").level_of_detail == "resource_parity"
        assert GrillingProfile(level_of_detail="3").level_of_detail == "senior_architect"

        assert GrillingProfile(visual_inclusion_threshold="strict").visual_inclusion_threshold == "strict_need_based"
        assert GrillingProfile(visual_inclusion_threshold="dense").visual_inclusion_threshold == "diagram_dense"

        assert GrillingProfile(audience_focus="production").audience_focus == "production_engineering"
        assert GrillingProfile(audience_focus="interview").audience_focus == "faang_interview"
        assert GrillingProfile(audience_focus="academic").audience_focus == "academic_foundations"

    def test_corrupted_json_string_raises_json_decode_error(self):
        """Malformed JSON raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            GrillingProfile.from_json("{ 'invalid': true, unquoted }")

    def test_non_dict_json_raises_attribute_error(self):
        """Non-dictionary JSON representations raise AttributeError."""
        with pytest.raises(AttributeError):
            GrillingProfile.from_json("12345")
        with pytest.raises(AttributeError):
            GrillingProfile.from_json("[\"level_of_detail\", \"foundations\"]")

    def test_file_load_and_save_deep_directory_creation(self, tmp_path):
        """Profile save creates non-existent parent directory trees reliably."""
        deep_target = tmp_path / "deep" / "nested" / "path" / "custom_profile.json"
        p = GrillingProfile(
            level_of_detail="foundations",
            visual_inclusion_threshold="balanced",
            audience_focus="production_engineering",
            domain_priorities=["v8_ignition", "turbofan"],
        )
        saved_path = p.save(deep_target)
        assert saved_path.exists()

        loaded = GrillingProfile.load(deep_target)
        assert loaded.level_of_detail == "foundations"
        assert loaded.visual_inclusion_threshold == "balanced"
        assert loaded.domain_priorities == ["v8_ignition", "turbofan"]


# ===========================================================================
# 3. Adversarial Domain Priorities Sanitization
# ===========================================================================

class TestAdversarialDomainPrioritiesSanitization:
    """Stress tests sanitization of injection attacks, capping, and boundaries."""

    def test_injection_characters_stripped(self):
        """Shell injection, SQL injection, and script tags are thoroughly sanitized."""
        injections = [
            '"; DROP TABLE profiles; --',
            '<script>alert("xss")</script>',
            '$(whoami)`touch /tmp/pwned`',
            'event_loop; rm -rf /',
            'topic#hash$dollar\\backslash',
            "'''quoted_value'''",
        ]
        sanitized = sanitize_domain_priorities(injections)
        for item in sanitized:
            assert ";" not in item
            assert "<" not in item
            assert ">" not in item
            assert "`" not in item
            assert "#" not in item
            assert "$" not in item
            assert "\\" not in item
            assert '"' not in item
            assert "'" not in item

    def test_massive_priority_list_capping_and_uniqueness(self):
        """List of 1,000 items is safely deduplicated and capped to max_count (20)."""
        massive = [f"topic_{i % 50}" for i in range(1000)]
        sanitized = sanitize_domain_priorities(massive, max_count=20)
        assert len(sanitized) == 20
        # All items must be unique
        assert len(set(sanitized)) == 20

    def test_case_insensitive_deduplication(self):
        """Preserves first occurrence while discarding duplicate case variations."""
        raw = ["event_loop", "Event_Loop", "EVENT_LOOP", "v8_internals", "V8_INTERNALS"]
        sanitized = sanitize_domain_priorities(raw)
        assert sanitized == ["event_loop", "v8_internals"]

    def test_non_string_elements_safely_ignored(self):
        """Non-string items (None, numbers, dicts) are discarded without crashing."""
        raw = [None, 123, {"bad": "type"}, "valid_topic_1", ["list"], "valid_topic_2"]
        sanitized = sanitize_domain_priorities(raw)
        assert sanitized == ["valid_topic_1", "valid_topic_2"]

    def test_empty_or_whitespace_only_fallback(self):
        """Empty lists, whitespace strings, or all-injection strings fall back to default priorities."""
        assert sanitize_domain_priorities([]) == DEFAULT_DOMAIN_PRIORITIES
        assert sanitize_domain_priorities(None) == DEFAULT_DOMAIN_PRIORITIES
        assert sanitize_domain_priorities(["", "   ", "\t\n"]) == DEFAULT_DOMAIN_PRIORITIES
        assert sanitize_domain_priorities([';;;"""<<<>>>']) == DEFAULT_DOMAIN_PRIORITIES

    def test_devanagari_characters_in_priorities_handled(self):
        """Devanagari characters in domain priorities are safely accepted or handled."""
        raw = ["इवेंट_लूप", "v8_internals", "जावास्क्रिप्ट"]
        sanitized = sanitize_domain_priorities(raw)
        assert "v8_internals" in sanitized
        assert len(sanitized) == 3

    def test_string_passed_instead_of_sequence_iterates_characters_behavior(self):
        """Empirically documents: passing string instead of list to sanitize_domain_priorities iterates characters."""
        result = sanitize_domain_priorities("event_loop, v8_internals")
        # In Python, str is a Sequence[str], so each char is sanitized & deduplicated
        assert isinstance(result, list)
        assert "e" in result
        assert "v" in result


# ===========================================================================
# 4. Adversarial GrillingEngine & Interview Flow
# ===========================================================================

class TestAdversarialGrillingEngine:
    """Stress tests interactive clarification interview and corpus integration."""

    def test_mandatory_image_clarification_banner_present_in_output(self):
        """Explicit clarification banner about video frames and slides MUST be presented."""
        printed_output: List[str] = []
        inputs = iter(["", "", "", ""])

        engine = GrillingEngine(
            input_fn=lambda _: next(inputs),
            print_fn=lambda msg: printed_output.append(str(msg)),
        )
        engine.conduct_interview(non_interactive=False)

        full_text = "\n".join(printed_output)
        assert "CLARIFICATION: In 'thenuke', 'images' specifically refers to captured" in full_text
        assert "video frames and presentation slides" in full_text
        assert "Strict Need-Based" in full_text

    def test_interview_recovers_from_repeated_invalid_inputs(self):
        """Engine rejects invalid choices and prompts again until valid option entered."""
        # LOD invalid attempts -> 3
        # VIT invalid attempts -> 1
        # Focus invalid attempts -> 2
        # Priorities -> enter
        inputs = iter([
            "bad_lod", "invalid", "3",
            "wrong_vit", "1",
            "bad_focus", "2",
            "",
        ])
        engine = GrillingEngine(
            input_fn=lambda _: next(inputs),
            print_fn=lambda _: None,
        )
        profile = engine.conduct_interview(non_interactive=False)
        assert profile.level_of_detail == "senior_architect"
        assert profile.visual_inclusion_threshold == "strict_need_based"
        assert profile.audience_focus == "faang_interview"

    def test_interview_graceful_recovery_on_eof_and_interrupt(self):
        """Engine gracefully falls back to default settings when stdin encounters EOF."""
        def raising_input(_):
            raise EOFError("simulated terminal disconnect")

        engine = GrillingEngine(
            input_fn=raising_input,
            print_fn=lambda _: None,
        )
        profile = engine.conduct_interview(non_interactive=False)
        assert profile.level_of_detail == "senior_architect"
        assert profile.visual_inclusion_threshold == "strict_need_based"
        assert profile.audience_focus == "faang_interview"

    def test_corpus_topic_extraction_with_corrupted_file(self, tmp_path):
        """Corrupted corpus file does not crash interview, falls back to default priorities."""
        bad_corpus = tmp_path / "corrupted_corpus.json"
        bad_corpus.write_text("{ not valid json content }", encoding="utf-8")

        profile = run_grilling_interview(
            corpus=bad_corpus,
            output_path=None,
            interactive=False,
        )
        assert profile.domain_priorities == DEFAULT_DOMAIN_PRIORITIES

    def test_corpus_topic_extraction_with_valid_corpus(self, tmp_path):
        """Valid corpus file populates suggested domain priorities."""
        valid_corpus = tmp_path / "valid_corpus.json"
        corpus_data = {
            "corpus_id": "test_c1",
            "aggregated_topics": ["turbofan", "ignition", "hidden_classes", "inline_cache"],
        }
        valid_corpus.write_text(json.dumps(corpus_data), encoding="utf-8")

        profile = run_grilling_interview(
            corpus=valid_corpus,
            output_path=None,
            interactive=False,
        )
        assert profile.domain_priorities == ["turbofan", "ignition", "hidden_classes", "inline_cache"]
