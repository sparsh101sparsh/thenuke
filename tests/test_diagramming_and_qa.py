"""Tests for Milestone 4 & 5: Vector Engine and QA Audit Engine.

Milestone 4 — Vector Diagramming & Branding Engine (vector_engine.py):
  - Palette token definitions (RGB tuples in [0,1] range).
  - Markdown block parser correctness.
  - Callout box label detection.
  - PDF compilation API (with PyMuPDF available or gracefully skipped).

Milestone 5 — QA Audit Engine (qa_audit_engine.py):
  - Pass 2 textual audit against synthesized Markdown (used as surrogate PDF text).
  - Devanagari violation detection in QA pass.
  - Syllabus index check.
  - Branding check.
  - ES2024+ signal detection.
  - Phase challenge block detection.
  - QA report JSON serialization.
  - Adversarial: inject Devanagari → Pass 2 must flag it.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.diagramming.vector_engine import (
    Palette,
    _parse_markdown_blocks,
    TextBlock,
    A4_WIDTH_PT,
    A4_HEIGHT_PT,
    MARGIN_PT,
    HEADER_TEXT,
    FOOTER_RIGHT,
)

from scripts.qa.qa_audit_engine import (
    run_pass2_textual,
    run_qa_audit,
    QAReport,
    Pass2TextualResult,
    _DEVANAGARI_RE,
    _SYLLABUS_SIGNAL_RE,
    _BRANDING_RE,
    _CHALLENGE_BLOCK_RE,
    _ES2024_SIGNALS,
)

from scripts.synthesis.manual_synthesizer import (
    SynthesisConfig,
    synthesize_manual,
    serialize_manual_to_markdown,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sample_markdown() -> str:
    config = SynthesisConfig(phases_to_include=[1, 5], include_appendices=True)
    manual = synthesize_manual(config)
    return serialize_manual_to_markdown(manual)


@pytest.fixture(scope="module")
def sample_md_file(sample_markdown, tmp_path_factory) -> Path:
    p = tmp_path_factory.mktemp("qa_test") / "sample_manual.md"
    p.write_text(sample_markdown, encoding="utf-8")
    return p


# ===========================================================================
# GROUP 1 — Palette Token Validation
# ===========================================================================

class TestPalette:

    def test_all_palette_colors_are_rgb_tuples(self):
        """Every Palette color must be a 3-tuple with values in [0.0, 1.0]."""
        for name in ["BLACK", "CHARCOAL", "DARK_GREY", "SLATE", "MUTED",
                     "HAIRLINE", "OFFWHITE", "CALLOUT_BG", "WHITE"]:
            color = getattr(Palette, name)
            assert isinstance(color, tuple), f"{name} is not a tuple"
            assert len(color) == 3, f"{name} does not have 3 channels"
            for ch in color:
                assert 0.0 <= ch <= 1.0, f"{name} channel out of [0,1]: {ch}"

    def test_black_is_pure_black(self):
        assert Palette.BLACK == (0.0, 0.0, 0.0)

    def test_white_is_pure_white(self):
        assert Palette.WHITE == (1.0, 1.0, 1.0)

    def test_hairline_width_less_than_border(self):
        assert Palette.HAIRLINE_WIDTH < Palette.BORDER_WIDTH

    def test_a4_dimensions_correct(self):
        """A4 must be 595.28 x 841.89 pt."""
        assert abs(A4_WIDTH_PT - 595.28) < 0.1
        assert abs(A4_HEIGHT_PT - 841.89) < 0.1

    def test_margin_is_54pt(self):
        assert MARGIN_PT == 54.0

    def test_content_width_is_a4_minus_two_margins(self):
        from scripts.diagramming.vector_engine import CONTENT_WIDTH
        assert abs(CONTENT_WIDTH - (A4_WIDTH_PT - 2 * MARGIN_PT)) < 0.1

    def test_header_text_contains_manual_title(self):
        assert "JavaScript" in HEADER_TEXT
        assert "Reference Manual" in HEADER_TEXT

    def test_footer_right_contains_monochrome(self):
        assert "Monochrome" in FOOTER_RIGHT


# ===========================================================================
# GROUP 2 — Markdown Block Parser
# ===========================================================================

class TestMarkdownBlockParser:

    def test_parse_simple_phase_header(self):
        md = "=============================\nPHASE 1: CORE FOUNDATIONS\n============================="
        blocks = _parse_markdown_blocks(md)
        headers = [b for b in blocks if b.kind == "phase_header"]
        assert any("PHASE 1" in b.text for b in headers), f"Phase header not found in: {blocks}"

    def test_parse_chapter_title(self):
        md = "### Chapter 1.1 — Variables: var, let, const"
        blocks = _parse_markdown_blocks(md)
        titles = [b for b in blocks if b.kind == "chapter_title"]
        assert len(titles) == 1
        assert "Chapter 1.1" in titles[0].text

    def test_parse_callout_block(self):
        md = "[MENTAL MODEL]\nThis is the mental model body text."
        blocks = _parse_markdown_blocks(md)
        callouts = [b for b in blocks if b.kind == "callout"]
        assert len(callouts) == 1
        assert callouts[0].extra == "[MENTAL MODEL]"
        assert "mental model body" in callouts[0].text

    def test_parse_code_fence(self):
        md = "Some prose.\n```javascript\nconst x = 42; // 42\n```\nMore prose."
        blocks = _parse_markdown_blocks(md)
        codes = [b for b in blocks if b.kind == "code"]
        assert len(codes) == 1
        assert "const x = 42" in codes[0].text

    def test_code_fence_does_not_split_on_hash_comments(self):
        """Code blocks must not be split on # inside fences."""
        md = "```python\n# Step 1\ndb = connect()\n# Step 2\nmigrate(db)\n```"
        blocks = _parse_markdown_blocks(md)
        codes = [b for b in blocks if b.kind == "code"]
        assert len(codes) == 1, f"Code block split into {len(codes)} pieces"
        assert "Step 1" in codes[0].text
        assert "Step 2" in codes[0].text

    def test_parse_challenge_line(self):
        md = "Challenge 1: Output Prediction & Trace Drill"
        blocks = _parse_markdown_blocks(md)
        challenges = [b for b in blocks if b.kind == "challenge"]
        assert len(challenges) == 1
        assert "Output Prediction" in challenges[0].text

    def test_parse_body_text(self):
        md = "Technically bolo toh... yeh ek simple explanation hai."
        blocks = _parse_markdown_blocks(md)
        body_blocks = [b for b in blocks if b.kind == "body"]
        assert body_blocks
        combined = " ".join(b.text for b in body_blocks)
        assert "Technically bolo toh" in combined

    def test_empty_markdown_produces_no_blocks(self):
        blocks = _parse_markdown_blocks("")
        assert blocks == []

    def test_multiple_callouts_parsed_independently(self):
        md = (
            "[MENTAL MODEL]\nFirst callout body.\n\n"
            "[ENGINEERING GOTCHA]\nSecond callout body."
        )
        blocks = _parse_markdown_blocks(md)
        callouts = [b for b in blocks if b.kind == "callout"]
        assert len(callouts) == 2
        labels = {c.extra for c in callouts}
        assert "[MENTAL MODEL]" in labels
        assert "[ENGINEERING GOTCHA]" in labels

    def test_adversarial_unclosed_code_fence(self):
        """Unclosed code fence must not crash the parser."""
        md = "Prose.\n```javascript\nconst x = 1;\n"
        blocks = _parse_markdown_blocks(md)
        # Should not raise; may produce a code block or absorb as body
        assert isinstance(blocks, list)


# ===========================================================================
# GROUP 3 — QA Pass 2: Textual Audit Regex Patterns
# ===========================================================================

class TestQAPass2Patterns:

    def test_devanagari_regex_matches_hindi(self):
        assert _DEVANAGARI_RE.search("है")
        assert _DEVANAGARI_RE.search("करो")
        assert not _DEVANAGARI_RE.search("karta hai")

    def test_syllabus_signal_regex(self):
        assert _SYLLABUS_SIGNAL_RE.search("DETAILED SYLLABUS & TABLE OF CONTENTS")
        assert _SYLLABUS_SIGNAL_RE.search("Detailed Syllabus Table of Contents")
        assert not _SYLLABUS_SIGNAL_RE.search("Random text here")

    def test_branding_regex(self):
        assert _BRANDING_RE.search("Prepared by @issparsh @sumitsingh097")
        assert _BRANDING_RE.search("PREPARED BY @ISSPARSH @SUMITSINGH097")
        assert not _BRANDING_RE.search("Prepared by @someone_else")

    def test_challenge_block_regex(self):
        assert _CHALLENGE_BLOCK_RE.search("Challenge 1: Output Prediction")
        assert _CHALLENGE_BLOCK_RE.search("challenge 3: Industrial Mini-Project")
        assert not _CHALLENGE_BLOCK_RE.search("The challenge is to implement")

    def test_es2024_signals_list_non_empty(self):
        assert len(_ES2024_SIGNALS) >= 5
        assert "Promise.withResolvers" in _ES2024_SIGNALS


# ===========================================================================
# GROUP 4 — QA Pass 2: Audit Against Synthesized Markdown
# ===========================================================================

class TestQAPass2Audit:

    def test_clean_manual_passes_pass2(self, sample_md_file):
        """A properly synthesized manual must pass Pass 2 with zero errors."""
        result = run_pass2_textual(sample_md_file)
        assert result.devanagari_violations == [], (
            f"Devanagari violations in clean manual: {result.devanagari_violations[:3]}"
        )
        assert result.has_syllabus_index
        assert result.branding_found
        assert result.passed
        assert result.error_count == 0

    def test_pass2_detects_devanagari_contamination(self, tmp_path):
        """Pass 2 must flag Devanagari characters in the text."""
        contaminated_path = tmp_path / "contaminated.md"
        contaminated_path.write_text(
            "DETAILED SYLLABUS & TABLE OF CONTENTS\n"
            "Prepared by @issparsh @sumitsingh097\n"
            "Challenge 1: Output Prediction\n"
            "Challenge 2: Algorithm\n"
            "Challenge 3: Industrial\n"
            "This text contains है a Devanagari violation.\n",
            encoding="utf-8",
        )
        result = run_pass2_textual(contaminated_path)
        assert result.devanagari_violations, "Pass 2 failed to detect Devanagari"
        assert result.error_count >= 1
        assert not result.passed

    def test_pass2_detects_missing_syllabus(self, tmp_path):
        """Pass 2 must flag missing syllabus index."""
        no_syllabus_path = tmp_path / "no_syllabus.md"
        no_syllabus_path.write_text(
            "Prepared by @issparsh @sumitsingh097\n"
            "Challenge 1: Output\nChallenge 2: Algo\nChallenge 3: Project\n"
            "PHASE 1: FOUNDATIONS\nPHASE 2: CONTROL FLOW\n",
            encoding="utf-8",
        )
        result = run_pass2_textual(no_syllabus_path)
        assert not result.has_syllabus_index
        assert result.error_count >= 1
        assert not result.passed

    def test_pass2_detects_missing_branding(self, tmp_path):
        """Pass 2 must flag missing author attribution."""
        no_brand_path = tmp_path / "no_brand.md"
        no_brand_path.write_text(
            "DETAILED SYLLABUS & TABLE OF CONTENTS\n"
            "Challenge 1: Output\nChallenge 2: Algo\nChallenge 3: Project\n"
            "PHASE 1: FOUNDATIONS\n",
            encoding="utf-8",
        )
        result = run_pass2_textual(no_brand_path)
        assert not result.branding_found
        assert result.error_count >= 1
        assert not result.passed

    def test_pass2_phase_count_detected(self, sample_md_file):
        """Phase count must be ≥ 2 for a 2-phase manual."""
        result = run_pass2_textual(sample_md_file)
        assert result.phase_count_detected >= 2

    def test_pass2_challenge_blocks_detected(self, sample_md_file):
        """Challenge blocks must be ≥ 6 (3 per phase × 2 phases)."""
        result = run_pass2_textual(sample_md_file)
        assert result.challenge_blocks_detected >= 6, (
            f"Only {result.challenge_blocks_detected} challenge blocks detected (expected ≥6)"
        )

    def test_pass2_es2024_signals_detected(self, sample_md_file):
        """Pass 2 must detect at least one ES2024+ signal in the manual."""
        result = run_pass2_textual(sample_md_file)
        assert result.es2024_signals_found, "No ES2024+ signals found in manual"

    def test_pass2_total_text_length_substantial(self, sample_md_file):
        """A 2-phase manual must have at least 5000 characters of text."""
        result = run_pass2_textual(sample_md_file)
        assert result.total_text_length >= 5000, (
            f"Manual text too short: {result.total_text_length} chars"
        )


# ===========================================================================
# GROUP 5 — Full QA Audit Report
# ===========================================================================

class TestQAReport:

    def test_run_qa_audit_returns_qa_report(self, sample_md_file):
        """run_qa_audit must return a QAReport dataclass."""
        report = run_qa_audit(sample_md_file)
        assert isinstance(report, QAReport)

    def test_qa_report_has_summary(self, sample_md_file):
        report = run_qa_audit(sample_md_file)
        assert report.summary
        assert len(report.summary) > 10

    def test_qa_report_clean_manual_passes(self, sample_md_file):
        report = run_qa_audit(sample_md_file)
        # Pass 2 (textual) must pass — Pass 1 (visual) only applies to real PDFs
        assert report.pass2_textual.passed, (
            f"QA Pass 2 failed for clean manual: {report.summary}"
        )
        assert report.pass2_textual.error_count == 0, (
            f"Pass 2 errors: {report.pass2_textual.error_count}"
        )

    def test_qa_report_json_written_to_disk(self, sample_md_file, tmp_path):
        report_path = tmp_path / "qa_report.json"
        run_qa_audit(sample_md_file, output_report_path=report_path)
        assert report_path.exists()
        data = json.loads(report_path.read_text())
        assert "overall_passed" in data
        assert "summary" in data
        assert "pass2_textual" in data

    def test_qa_report_json_is_valid_json(self, sample_md_file, tmp_path):
        report_path = tmp_path / "qa_report.json"
        run_qa_audit(sample_md_file, output_report_path=report_path)
        raw = report_path.read_text()
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)

    def test_qa_report_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            run_qa_audit(tmp_path / "nonexistent.pdf")

    def test_qa_report_contaminated_fails(self, tmp_path):
        bad_path = tmp_path / "bad.md"
        bad_path.write_text("है this is bad.\nNo syllabus here.\n", encoding="utf-8")
        report = run_qa_audit(bad_path)
        assert not report.overall_passed
        assert not report.pass2_textual.passed
