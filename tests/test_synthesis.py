"""Tests for Milestone 3: Reference Manual Synthesis Engine.

Covers:
- Zero Devanagari enforcement (critical constraint).
- Syllabus index structure and content.
- Phase chapter rendering.
- 3-part Phase Challenge presence and integrity.
- Roman Hinglish bridge phrases present.
- ES2024+ signals in challenge prompts.
- Callout label validation.
- Adversarial: Devanagari injection detection.
- Adversarial: Missing phase challenge raises ValueError.
- Adversarial: Config with invalid phase numbers.
"""

from __future__ import annotations

import re
import pytest

# ---------------------------------------------------------------------------
# Import the synthesizer module under test
# ---------------------------------------------------------------------------

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.synthesis.manual_synthesizer import (
    SynthesisConfig,
    PhaseChallenge,
    PHASE_CATALOG,
    ROMAN_HINGLISH_BRIDGES,
    _DEVANAGARI_PATTERN,
    validate_zero_devanagari,
    assert_zero_devanagari,
    generate_syllabus_index,
    get_phase_challenge,
    render_phase,
    synthesize_manual,
    serialize_manual_to_markdown,
    SynthesizedManual,
    APPENDICES,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def default_config() -> SynthesisConfig:
    return SynthesisConfig(
        topic="JavaScript",
        level_of_detail="senior_architect",
        visual_threshold="strict_need_based",
        audience_focus="faang_interview",
        phases_to_include=list(range(1, 10)),
        include_appendices=True,
    )


@pytest.fixture(scope="module")
def full_manual(default_config) -> SynthesizedManual:
    return synthesize_manual(default_config)


@pytest.fixture(scope="module")
def full_markdown(full_manual) -> str:
    return serialize_manual_to_markdown(full_manual)


# ===========================================================================
# GROUP 1 — Zero Devanagari (Critical Constraint)
# ===========================================================================

class TestZeroDevanagari:

    def test_devanagari_pattern_detects_hindi_chars(self):
        """CRITICAL: Pattern must catch Devanagari Unicode characters."""
        sample = "kya hai ye"
        assert not _DEVANAGARI_PATTERN.search(sample), "False positive on Latin text"

        hindi_samples = ["है", "करो", "या", "देवनागरी", "नमस्ते"]
        for s in hindi_samples:
            assert _DEVANAGARI_PATTERN.search(s), f"Failed to detect Devanagari in: {s!r}"

    def test_validate_zero_devanagari_clean_text(self):
        """Clean Roman text must return empty violations list."""
        clean = "Technically bolo toh... Call Stack, Memory Heap, Lexical Environment Record."
        violations = validate_zero_devanagari(clean)
        assert violations == [], f"False violations on clean text: {violations}"

    def test_validate_zero_devanagari_detects_violation(self):
        """Single Devanagari character must be reported."""
        contaminated = "This is a है violation"
        violations = validate_zero_devanagari(contaminated)
        assert len(violations) >= 1
        assert "U+0939" in violations[0] or "0939" in violations[0]

    def test_assert_zero_devanagari_raises_on_violation(self):
        """assert_zero_devanagari must raise ValueError on Devanagari."""
        with pytest.raises(ValueError, match="DEVANAGARI VIOLATION"):
            assert_zero_devanagari("text with करो embedded", context="test")

    def test_assert_zero_devanagari_passes_on_clean(self):
        """assert_zero_devanagari must not raise on clean Roman text."""
        assert_zero_devanagari("Sabse pehle ye samajhna zaroori hai ki Call Stack exists.", context="test")

    def test_full_manual_markdown_zero_devanagari(self, full_markdown):
        """CRITICAL: The entire synthesized manual must contain zero Devanagari chars."""
        violations = validate_zero_devanagari(full_markdown)
        assert violations == [], (
            f"Devanagari found in full manual output ({len(violations)} occurrence(s)):\n"
            + "\n".join(violations[:5])
        )

    def test_syllabus_index_zero_devanagari(self, full_manual):
        """Syllabus index must be fully Roman-script."""
        violations = validate_zero_devanagari(full_manual.syllabus_index)
        assert violations == [], f"Devanagari in syllabus_index: {violations[:3]}"

    def test_phase_challenge_prompts_zero_devanagari(self):
        """All 9 phase challenge prompt texts must be Devanagari-free."""
        for phase_num in range(1, 10):
            ch = get_phase_challenge(phase_num)
            for attr in [ch.challenge_1_prompt, ch.challenge_2_prompt, ch.challenge_3_prompt]:
                violations = validate_zero_devanagari(attr)
                assert violations == [], (
                    f"Devanagari in Phase {phase_num} challenge: {violations[:2]}"
                )

    def test_adversarial_devanagari_injection_in_topic(self):
        """Injecting Devanagari in topic field must be caught during synthesis."""
        bad_config = SynthesisConfig(
            topic="JavaScript है",
            phases_to_include=[1],
        )
        with pytest.raises(ValueError, match="DEVANAGARI VIOLATION"):
            manual = synthesize_manual(bad_config)
            serialize_manual_to_markdown(manual)


# ===========================================================================
# GROUP 2 — Syllabus Index Structure
# ===========================================================================

class TestSyllabusIndex:

    def test_syllabus_index_present_in_manual(self, full_manual):
        """SynthesizedManual must have a non-empty syllabus_index field."""
        assert full_manual.syllabus_index
        assert len(full_manual.syllabus_index) > 200

    def test_syllabus_index_contains_all_parts(self, full_manual):
        """Syllabus index must include PART I through PART III (3 groups of 3 phases)."""
        syllabus = full_manual.syllabus_index
        assert "PART I" in syllabus
        assert "PART II" in syllabus
        assert "PART III" in syllabus

    def test_syllabus_index_lists_all_9_phases(self, full_manual):
        """All 9 phases must be listed in the syllabus index."""
        syllabus = full_manual.syllabus_index
        for phase_num in range(1, 10):
            assert f"Phase {phase_num}:" in syllabus, (
                f"Phase {phase_num} missing from syllabus index"
            )

    def test_syllabus_index_contains_challenge_breakdown(self, full_manual):
        """Each phase in the syllabus must list all 3 Challenge types."""
        syllabus = full_manual.syllabus_index
        assert "Challenge 1: Output Prediction" in syllabus
        assert "Challenge 2: Algorithm" in syllabus
        assert "Challenge 3: Industrial Mini-Project" in syllabus

    def test_syllabus_header_present_in_markdown(self, full_markdown):
        """Full manual Markdown must contain the DETAILED SYLLABUS header."""
        assert "DETAILED SYLLABUS" in full_markdown
        assert "TABLE OF CONTENTS" in full_markdown

    def test_appendices_listed_in_syllabus(self, full_manual):
        """Syllabus must list the V8, OWASP, and Machine Coding appendices."""
        syllabus = full_manual.syllabus_index
        assert "Appendix A" in syllabus or "APPENDICES" in syllabus
        assert "V8" in syllabus
        assert "OWASP" in syllabus

    def test_generate_syllabus_index_empty_phases(self):
        """generate_syllabus_index with no phases must still produce a header."""
        result = generate_syllabus_index([], [])
        assert "DETAILED SYLLABUS" in result
        assert "TABLE OF CONTENTS" in result


# ===========================================================================
# GROUP 3 — Phase Rendering
# ===========================================================================

class TestPhaseRendering:

    def test_manual_has_correct_phase_count(self, full_manual):
        """Manual must contain exactly 9 rendered phases."""
        assert len(full_manual.phases) == 9

    def test_phase_titles_match_catalog(self, full_manual):
        """Rendered phase titles must match the PHASE_CATALOG definitions."""
        catalog_titles = {p["number"]: p["title"] for p in PHASE_CATALOG}
        for phase in full_manual.phases:
            assert phase.title == catalog_titles[phase.number], (
                f"Phase {phase.number} title mismatch: {phase.title!r} != {catalog_titles[phase.number]!r}"
            )

    def test_phase_chapters_non_empty(self, full_manual):
        """Every rendered phase must have at least one chapter."""
        for phase in full_manual.phases:
            assert len(phase.chapters) >= 1, f"Phase {phase.number} has no chapters"

    def test_phase_chapter_bodies_non_empty(self, full_manual):
        """Every chapter body must be non-empty."""
        for phase in full_manual.phases:
            for ch in phase.chapters:
                assert ch.body_markdown.strip(), (
                    f"Phase {phase.number} Chapter {ch.chapter_index} has empty body"
                )

    def test_phase_topics_bar_present_in_chapter(self, full_manual):
        """Chapter bodies must contain the 'Topics:' bar."""
        for phase in full_manual.phases:
            for ch in phase.chapters:
                assert "Topics:" in ch.body_markdown, (
                    f"Phase {phase.number} Ch {ch.chapter_index} missing 'Topics:' bar"
                )

    def test_roman_hinglish_bridge_phrases_in_chapters(self, full_manual):
        """At least one Roman Hinglish bridge phrase must appear in each phase's chapter bodies."""
        bridge_pattern = re.compile(
            "|".join(re.escape(b) for b in ROMAN_HINGLISH_BRIDGES),
            re.IGNORECASE,
        )
        for phase in full_manual.phases:
            all_body = " ".join(ch.body_markdown for ch in phase.chapters)
            assert bridge_pattern.search(all_body), (
                f"Phase {phase.number} has no Roman Hinglish bridge phrases"
            )

    def test_mental_model_callout_present(self, full_manual):
        """[MENTAL MODEL] callout must appear in every chapter body."""
        for phase in full_manual.phases:
            for ch in phase.chapters:
                assert "[MENTAL MODEL]" in ch.body_markdown, (
                    f"Phase {phase.number} Ch {ch.chapter_index} missing [MENTAL MODEL]"
                )

    def test_engineering_gotcha_callout_present(self, full_manual):
        """[ENGINEERING GOTCHA] callout must appear in every chapter body."""
        for phase in full_manual.phases:
            for ch in phase.chapters:
                assert "[ENGINEERING GOTCHA]" in ch.body_markdown, (
                    f"Phase {phase.number} Ch {ch.chapter_index} missing [ENGINEERING GOTCHA]"
                )

    def test_interview_tip_present_for_faang_config(self, full_manual):
        """[INTERVIEW TIP] must appear in chapters when audience_focus is faang_interview."""
        for phase in full_manual.phases:
            for ch in phase.chapters:
                assert "[INTERVIEW TIP]" in ch.body_markdown, (
                    f"Phase {phase.number} Ch {ch.chapter_index} missing [INTERVIEW TIP] (faang config)"
                )

    def test_phases_in_markdown_sorted_numerically(self, full_markdown):
        """Phase headers must appear in ascending order 1→9 in the output Markdown."""
        positions = []
        for i in range(1, 10):
            pos = full_markdown.find(f"PHASE {i}")
            assert pos != -1, f"PHASE {i} not found in markdown output"
            positions.append(pos)
        assert positions == sorted(positions), "Phases are not in ascending order in markdown"


# ===========================================================================
# GROUP 4 — Phase Challenges (3-Part Mandatory Drills)
# ===========================================================================

class TestPhaseChallenges:

    @pytest.mark.parametrize("phase_num", list(range(1, 10)))
    def test_challenge_exists_for_each_phase(self, phase_num):
        """get_phase_challenge must return a PhaseChallenge for all 9 phases."""
        ch = get_phase_challenge(phase_num)
        assert isinstance(ch, PhaseChallenge)
        assert ch.phase_number == phase_num

    @pytest.mark.parametrize("phase_num", list(range(1, 10)))
    def test_all_three_challenge_titles_non_empty(self, phase_num):
        """All 3 challenge titles must be non-empty strings."""
        ch = get_phase_challenge(phase_num)
        assert ch.challenge_1_title.strip()
        assert ch.challenge_2_title.strip()
        assert ch.challenge_3_title.strip()

    @pytest.mark.parametrize("phase_num", list(range(1, 10)))
    def test_all_three_challenge_prompts_non_empty(self, phase_num):
        """All 3 challenge prompts must be substantial (>= 100 chars each)."""
        ch = get_phase_challenge(phase_num)
        for attr_name, attr_val in [
            ("challenge_1_prompt", ch.challenge_1_prompt),
            ("challenge_2_prompt", ch.challenge_2_prompt),
            ("challenge_3_prompt", ch.challenge_3_prompt),
        ]:
            assert len(attr_val) >= 100, (
                f"Phase {phase_num} {attr_name} is too short ({len(attr_val)} chars)"
            )

    def test_challenge_1_is_output_prediction(self):
        """Challenge 1 for every phase must be an Output Prediction drill."""
        for phase_num in range(1, 10):
            ch = get_phase_challenge(phase_num)
            assert "Output Prediction" in ch.challenge_1_title or "Trace" in ch.challenge_1_title, (
                f"Phase {phase_num} Challenge 1 is not an Output Prediction drill: {ch.challenge_1_title!r}"
            )

    def test_challenge_2_is_algorithm(self):
        """Challenge 2 for every phase must be an Algorithm or utility implementation."""
        for phase_num in range(1, 10):
            ch = get_phase_challenge(phase_num)
            assert any(k in ch.challenge_2_title for k in ["Algorithm", "Implement", "Zero-Dependency"]), (
                f"Phase {phase_num} Challenge 2 does not look like an algorithm drill: {ch.challenge_2_title!r}"
            )

    def test_challenge_3_is_industrial_mini_project(self):
        """Challenge 3 for every phase must be an Industrial Mini-Project."""
        for phase_num in range(1, 10):
            ch = get_phase_challenge(phase_num)
            assert "Industrial Mini-Project" in ch.challenge_3_title or "Project" in ch.challenge_3_title, (
                f"Phase {phase_num} Challenge 3 is not an Industrial Mini-Project: {ch.challenge_3_title!r}"
            )

    def test_challenge_prompts_require_zero_dependencies(self):
        """At least Challenge 2 per phase must specify zero dependencies."""
        for phase_num in range(1, 10):
            ch = get_phase_challenge(phase_num)
            combined = ch.challenge_2_prompt + ch.challenge_3_prompt
            assert "zero" in combined.lower() or "Zero" in combined, (
                f"Phase {phase_num} Challenge 2/3 do not mention zero dependencies"
            )

    def test_adversarial_invalid_phase_raises(self):
        """get_phase_challenge must raise ValueError for out-of-range phase numbers."""
        with pytest.raises(ValueError):
            get_phase_challenge(0)
        with pytest.raises(ValueError):
            get_phase_challenge(10)
        with pytest.raises(ValueError):
            get_phase_challenge(99)

    def test_challenges_present_in_full_markdown(self, full_markdown):
        """All 9 phases must have their challenge blocks in the serialized Markdown."""
        for phase_num in range(1, 10):
            assert f"PHASE {phase_num} — END-OF-PHASE CHALLENGES" in full_markdown, (
                f"Phase {phase_num} challenge block missing from Markdown output"
            )

    def test_all_three_challenge_types_present_per_phase_in_markdown(self, full_markdown):
        """Challenge 1, 2, and 3 headers must appear at least 9 times each in full markdown."""
        for challenge_num in [1, 2, 3]:
            count = full_markdown.count(f"Challenge {challenge_num}:")
            assert count >= 9, (
                f"Challenge {challenge_num} appears only {count} time(s) — expected ≥9"
            )


# ===========================================================================
# GROUP 5 — ES2024+ Code Policy
# ===========================================================================

class TestES2024Policy:

    def test_challenge_prompts_reference_es2024_features(self):
        """Challenge prompts must reference at least one ES2024+ API or feature."""
        es2024_signals = [
            "ES2024",
            "Promise.withResolvers",
            "Object.groupBy",
            "toSorted",
            "toReversed",
            "toSpliced",
            ".with(",
        ]
        all_challenge_text = ""
        for phase_num in range(1, 10):
            ch = get_phase_challenge(phase_num)
            all_challenge_text += ch.challenge_1_prompt + ch.challenge_2_prompt + ch.challenge_3_prompt

        found = [sig for sig in es2024_signals if sig in all_challenge_text]
        assert found, f"No ES2024+ API references found in any challenge prompt"

    def test_challenge_prompts_ban_foo_bar(self):
        """Anti-toy-code policy: challenge prompts must not use foo/bar placeholder names."""
        for phase_num in range(1, 10):
            ch = get_phase_challenge(phase_num)
            combined = (
                ch.challenge_1_prompt + ch.challenge_2_prompt + ch.challenge_3_prompt
            ).lower()
            assert "foo(" not in combined, (
                f"Phase {phase_num} challenge uses toy name 'foo'"
            )
            assert "bar(" not in combined, (
                f"Phase {phase_num} challenge uses toy name 'bar'"
            )


# ===========================================================================
# GROUP 6 — Branding & Metadata
# ===========================================================================

class TestBrandingMetadata:

    def test_cover_branding_present_in_markdown(self, full_markdown):
        """Markdown output must contain the mandatory attribution line."""
        assert "Prepared by @issparsh @sumitsingh097" in full_markdown

    def test_manual_topic_field_set(self, full_manual):
        """SynthesizedManual.topic must match config.topic."""
        assert full_manual.topic == "JavaScript"

    def test_manual_generated_at_is_iso8601(self, full_manual):
        """generated_at must be a valid ISO 8601 timestamp string."""
        from datetime import datetime
        # Should not raise
        datetime.fromisoformat(full_manual.generated_at.replace("Z", "+00:00"))

    def test_appendix_index_present_when_enabled(self, full_manual):
        """appendix_index must be non-empty when include_appendices=True."""
        assert full_manual.appendix_index
        assert "V8" in full_manual.appendix_index or "Appendix" in full_manual.appendix_index

    def test_manual_config_stored_correctly(self, full_manual, default_config):
        """Config stored in manual must match the input config."""
        assert full_manual.config.level_of_detail == default_config.level_of_detail
        assert full_manual.config.audience_focus == default_config.audience_focus


# ===========================================================================
# GROUP 7 — Adversarial Edge Cases
# ===========================================================================

class TestSynthesisAdversarial:

    def test_single_phase_config(self):
        """Synthesizing with only Phase 5 must produce exactly 1 phase."""
        config = SynthesisConfig(phases_to_include=[5])
        manual = synthesize_manual(config)
        assert len(manual.phases) == 1
        assert manual.phases[0].number == 5

    def test_no_appendices_config(self):
        """include_appendices=False must produce empty appendix_index."""
        config = SynthesisConfig(phases_to_include=[1], include_appendices=False)
        manual = synthesize_manual(config)
        assert manual.appendix_index == ""

    def test_markdown_serialization_is_deterministic(self, default_config):
        """Two calls to synthesize+serialize must produce structurally identical output."""
        m1 = synthesize_manual(default_config)
        m2 = synthesize_manual(default_config)
        md1 = serialize_manual_to_markdown(m1)
        md2 = serialize_manual_to_markdown(m2)
        # Remove timestamps before comparing
        ts_re = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\s]+")
        md1_clean = ts_re.sub("TIMESTAMP", md1)
        md2_clean = ts_re.sub("TIMESTAMP", md2)
        assert md1_clean == md2_clean, "Serialization is not deterministic"

    def test_audience_focus_academic_no_interview_tip(self):
        """Academic audience focus must NOT inject [INTERVIEW TIP] callouts."""
        config = SynthesisConfig(
            phases_to_include=[1],
            audience_focus="academic_foundations",
        )
        manual = synthesize_manual(config)
        for phase in manual.phases:
            for ch in phase.chapters:
                assert "[INTERVIEW TIP]" not in ch.body_markdown, (
                    f"[INTERVIEW TIP] present in academic_foundations config"
                )

    def test_full_markdown_no_foo_bar_identifiers(self, full_markdown):
        """Anti-toy-code: full markdown must not contain 'foo(' or 'bar(' identifiers."""
        assert "foo(" not in full_markdown.lower()
        assert "bar(" not in full_markdown.lower()

    def test_phase_catalog_covers_all_9_phases(self):
        """PHASE_CATALOG must define exactly 9 phases numbered 1–9."""
        numbers = sorted(p["number"] for p in PHASE_CATALOG)
        assert numbers == list(range(1, 10)), f"PHASE_CATALOG phase numbers: {numbers}"
