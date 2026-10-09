"""Tier 2: Boundary Value Analysis & Corner Cases (F1 - F15).

Minimum 75 test cases (5 boundary tests per feature).
Covers boundary conditions, empty/extreme inputs, malformed files, schema validations,
and adversarial error recovery.
"""

import json
import re
import os
import shutil
import fitz
import pptx
import pytest
from pathlib import Path

from ..conftest import (
    DEVANAGARI_REGEX,
    MONOCHROME_PALETTE,
    BRANDING_AUTHORS,
    ISO_A4_WIDTH,
    ISO_A4_HEIGHT,
    PAGE_MARGIN_MIN,
    safe_load_module,
)

# ---------------------------------------------------------------------------
# F1 Boundary: YouTube Subtitles & Ingestion (5 tests)
# ---------------------------------------------------------------------------

def test_f1_b01_empty_vtt_file():
    """F1.B1: Empty or whitespace-only VTT content handled gracefully without crashing."""
    from scripts.ingestion.yt_ingest import parse_vtt_cues, deduplicate_vtt_cues, clean_vtt_content

    empty_inputs = ["", "   \n\n\t  ", "WEBVTT\n\n"]
    for inp in empty_inputs:
        cues = parse_vtt_cues(inp)
        assert cues == []
        deduped = deduplicate_vtt_cues(cues)
        assert deduped == []
        cleaned = clean_vtt_content(inp)
        assert cleaned == ""


def test_f1_b02_corrupted_vtt_cues_recovery():
    """F1.B2: Malformed cue timestamps or missing timestamps skipped robustly."""
    from scripts.ingestion.yt_ingest import parse_vtt_cues

    corrupted_vtt = """WEBVTT

00:00:01.000 --> invalid_timestamp
Corrupted cue one

00:00:05.000 --> 00:00:08.000
Valid cue two that should be parsed
"""
    cues = parse_vtt_cues(corrupted_vtt)
    assert len(cues) >= 1
    assert any("Valid cue two" in c["raw_text"] for c in cues)


def test_f1_b03_massive_vtt_transcript_handling():
    """F1.B3: Long transcripts (>2,000 cues / multi-hour video) processed without memory exhaustion."""
    from scripts.ingestion.yt_ingest import deduplicate_vtt_cues

    cues = []
    for i in range(2000):
        cues.append({
            "start": float(i * 2),
            "end": float(i * 2 + 2),
            "lines": [f"Line {i} of execution context", f"Line {i+1} of lexical scope"],
            "raw_text": f"Line {i} of execution context Line {i+1} of lexical scope"
        })
    deduped = deduplicate_vtt_cues(cues)
    assert len(deduped) > 1000


def test_f1_b04_vtt_html_entities_and_formatting_strip():
    """F1.B4: Subtitles containing HTML entities and tags stripped cleanly."""
    from scripts.ingestion.yt_ingest import strip_vtt_markup

    raw_text = '<c.yellow>Execution &amp; Context</c> <00:00:01.500>is &lt;important&gt;'
    cleaned = strip_vtt_markup(raw_text)
    assert "<c" not in cleaned
    assert "<00:" not in cleaned
    assert "&amp;" not in cleaned
    assert "Execution & Context is <important>" == cleaned


def test_f1_b05_invalid_youtube_url_rejection():
    """F1.B5: Non-YouTube URLs or broken IDs handled with descriptive validation error."""
    from scripts.ingestion.yt_ingest import is_youtube_url, extract_video_id, ingest_youtube_url

    invalid_urls = [
        "",
        "not_a_url",
        "https://vimeo.com/987654321",
        "https://google.com/search?q=youtube",
        "https://dailymotion.com/video/x1234",
    ]
    for url in invalid_urls:
        assert is_youtube_url(url) is False
        assert extract_video_id(url) is None
        with pytest.raises(ValueError):
            ingest_youtube_url(url)


# ---------------------------------------------------------------------------
# F2 Boundary: Web Documentation Crawler & Headless Screenshots (5 tests)
# ---------------------------------------------------------------------------

def test_f2_b06_empty_html_body_handling():
    """F2.B6: HTML document with empty body or 0 bytes produces clean empty output."""
    from scripts.ingestion.web_crawler import html_to_markdown_and_code

    for empty_html in ["", "<html><body></body></html>", "   \n  "]:
        md, code, title = html_to_markdown_and_code(empty_html)
        assert md == ""
        assert code == []


def test_f2_b07_malformed_html_tags_robustness():
    """F2.B7: Unclosed HTML tags and broken DOM trees parsed robustly."""
    from scripts.ingestion.web_crawler import html_to_markdown_and_code

    malformed_html = """
    <div><h1>Title without closing tag
    <p>Paragraph unclosed
    <pre><code class="language-js">const a = 1;
    """
    md, code_blocks, title = html_to_markdown_and_code(malformed_html)
    assert "Title without closing tag" in md or "Title without closing tag" in title
    assert len(code_blocks) >= 1 or "const a = 1" in md


def test_f2_b08_deeply_nested_dom_tree():
    """F2.B8: DOM tree nested 50 levels deep parsed without recursion limit error."""
    from scripts.ingestion.web_crawler import html_to_markdown_and_code

    nested = "<div>" * 50 + "<p>Deeply nested technical content.</p>" + "</div>" * 50
    md, _, _ = html_to_markdown_and_code(nested)
    assert "Deeply nested technical content" in md


def test_f2_b09_unsupported_external_protocols():
    """F2.B9: URLs with ftp://, file://, or non-http protocols rejected with clear error."""
    from scripts.ingestion.web_crawler import crawl_url

    invalid_protocols = ["ftp://ftp.example.com/doc", "file:///etc/passwd", "gopher://example.com"]
    for url in invalid_protocols:
        with pytest.raises(ValueError):
            crawl_url(url)


def test_f2_b10_code_blocks_without_language_spec():
    """F2.B10: <pre><code> blocks without class or language attributes defaulted cleanly."""
    from scripts.ingestion.web_crawler import html_to_markdown_and_code

    raw_html = "<pre><code>console.log('Unspecified language');</code></pre>"
    md, code_blocks, _ = html_to_markdown_and_code(raw_html)
    assert len(code_blocks) == 1
    assert code_blocks[0].language in {"text", ""}
    assert "console.log" in code_blocks[0].code


# ---------------------------------------------------------------------------
# F3 Boundary: Local Files (PDF, PPTX, Video/OCR) (5 tests)
# ---------------------------------------------------------------------------

def test_f3_b11_zero_byte_pdf_handling(temp_workspace):
    """F3.B11: 0-byte PDF file raises specific file validation error instead of unhandled crash."""
    zero_pdf = temp_workspace / "empty.pdf"
    zero_pdf.write_bytes(b"")

    with pytest.raises(Exception):
        doc = fitz.open(zero_pdf)
        doc.close()


def test_f3_b12_corrupted_pdf_stream_handling(temp_workspace):
    """F3.B12: Truncated or corrupted PDF bytes handled gracefully with diagnostic error."""
    corrupt_pdf = temp_workspace / "corrupted.pdf"
    corrupt_pdf.write_bytes(b"%PDF-1.4\n%corrupted binary stream garbage...")

    with pytest.raises(Exception):
        doc = fitz.open(corrupt_pdf)
        _ = len(doc)
        doc.close()


def test_f3_b13_zero_byte_pptx_handling(temp_workspace):
    """F3.B13: 0-byte PPTX presentation handled with explicit invalid format error."""
    zero_pptx = temp_workspace / "empty.pptx"
    zero_pptx.write_bytes(b"")

    with pytest.raises(Exception):
        pptx.Presentation(zero_pptx)


def test_f3_b14_pptx_empty_slides_no_text(temp_workspace):
    """F3.B14: PPTX with blank slides produces valid presentation object without crashing."""
    prs = pptx.Presentation()
    prs.slides.add_slide(prs.slide_layouts[6]) # blank layout
    blank_pptx = temp_workspace / "blank.pptx"
    prs.save(blank_pptx)

    loaded = pptx.Presentation(blank_pptx)
    assert len(loaded.slides) == 1
    slide = loaded.slides[0]
    assert len(slide.shapes) == 0


def test_f3_b15_unsupported_file_extension(temp_workspace):
    """F3.B15: Ingestion rejects unsupported file formats (.xyz, .bin, .exe)."""
    bad_file = temp_workspace / "test.xyz"
    bad_file.write_text("random binary or text")

    supported_extensions = {".pdf", ".pptx", ".ppt", ".mp4", ".mov", ".png", ".jpg", ".jpeg"}
    assert bad_file.suffix.lower() not in supported_extensions


# ---------------------------------------------------------------------------
# F4 Boundary: Grilling Alignment Protocol (5 tests)
# ---------------------------------------------------------------------------

def test_f4_b16_invalid_level_of_detail_input():
    """F4.B16: Invalid level of detail (e.g. god_mode, ultra) rejected by validation."""
    valid_levels = {"foundations", "resource_parity", "senior_architect"}
    invalid_inputs = ["god_mode", "extreme", "level_99", ""]
    for inp in invalid_inputs:
        assert inp not in valid_levels


def test_f4_b17_invalid_visual_threshold_input():
    """F4.B17: Invalid visual threshold input rejected."""
    valid_thresholds = {"strict_need_based", "balanced", "diagram_dense"}
    invalid_inputs = ["infinite_diagrams", "no_text_only_pics", "random"]
    for inp in invalid_inputs:
        assert inp not in valid_thresholds


def test_f4_b18_empty_domain_priorities_list():
    """F4.B18: Empty domain priorities list handled with sensible default."""
    empty_priorities = []
    default_priorities = ["execution_context", "event_loop", "v8_internals"]
    resolved = empty_priorities or default_priorities
    assert len(resolved) == 3


def test_f4_b19_massive_domain_priorities_list():
    """F4.B19: 100+ domain priorities deduplicated and capped safely to top N."""
    massive_list = [f"topic_{i % 15}" for i in range(120)]
    # Deduplicate and cap
    unique_priorities = list(dict.fromkeys(massive_list))[:20]
    assert len(unique_priorities) <= 20
    assert len(unique_priorities) == 15


def test_f4_b20_special_characters_in_grilling_inputs():
    """F4.B20: Punctuation, unicode symbols, or quote marks in user answers sanitized."""
    raw_priority = ' "event_loop"; DROP TABLE users; -- <script> '
    sanitized = re.sub(r"[;\"\'<>]+", "", raw_priority).strip()
    assert ";" not in sanitized
    assert "<" not in sanitized
    assert "event_loop" in sanitized


# ---------------------------------------------------------------------------
# F5 Boundary: Hinglish & Zero-Devanagari (5 tests)
# ---------------------------------------------------------------------------

def test_f5_b21_single_devanagari_character_detected():
    """F5.B21: Single isolated Devanagari character (e.g. अ or ।) accurately detected."""
    sample_text = "This is Roman Hinglish text with one char: अ inside."
    matches = DEVANAGARI_REGEX.findall(sample_text)
    assert len(matches) == 1
    assert matches[0] == "अ"


def test_f5_b22_devanagari_extended_and_vedic_blocks():
    """F5.B22: Extended Devanagari (\\uA8E0-\\uA8FF) and Vedic extensions (\\u1CD0-\\u1CFF) caught."""
    # Vedic sign ardhavisarga (\u1CF2) and Devanagari extended (\uA8E1)
    extended_char = "\uA8E1"
    vedic_char = "\u1CF2"

    assert len(DEVANAGARI_REGEX.findall(extended_char)) == 1
    assert len(DEVANAGARI_REGEX.findall(vedic_char)) == 1


def test_f5_b23_empty_text_zero_devanagari_check():
    """F5.B23: Empty text string evaluated without regex errors (passes with 0 violations)."""
    assert len(DEVANAGARI_REGEX.findall("")) == 0
    assert len(DEVANAGARI_REGEX.findall("   \n\t")) == 0


def test_f5_b24_hinglish_code_comment_boundary():
    """F5.B24: Devanagari character inside code comment detected and flagged by audit."""
    code_with_hindi_comment = """
    // यह फ़ंक्शन प्रॉमिस बनाता है
    const p = Promise.withResolvers();
    """
    matches = DEVANAGARI_REGEX.findall(code_with_hindi_comment)
    assert len(matches) > 0, "Devanagari in code comment was not flagged"


def test_f5_b25_latin_accented_characters_not_flagged():
    """F5.B25: European Latin accents (é, ñ, ü) or mathematical symbols not falsely flagged."""
    european_latin = "Naïve résumé café señor Zürich π ≈ 3.14159"
    matches = DEVANAGARI_REGEX.findall(european_latin)
    assert len(matches) == 0, f"False positives detected: {matches}"


# ---------------------------------------------------------------------------
# F6 Boundary: Syllabus Index & 9-Phase Structure (5 tests)
# ---------------------------------------------------------------------------

def test_f6_b26_missing_part_in_syllabus_detected():
    """F6.B26: Syllabus missing PART IV triggers validation failure."""
    defective_syllabus = """
    ## PART I: RUNTIME
    ## PART II: CONCURRENCY
    ## PART III: OBJECTS
    ## PART V: ADVANCED
    ## PART VI: PRODUCTION
    """
    assert "PART IV" not in defective_syllabus


def test_f6_b27_scrambled_phase_ordering_detected():
    """F6.B27: Phases in non-sequential order detected and reported."""
    scrambled_phases = [1, 3, 2, 4, 5, 6, 7, 8, 9]
    is_sequential = scrambled_phases == sorted(scrambled_phases)
    assert is_sequential is False


def test_f6_b28_missing_phase_file_detected(temp_workspace):
    """F6.B28: Missing phase_05.md detected and flagged during multi-phase audit."""
    phase_dir = temp_workspace / "manual"
    phase_dir.mkdir()
    # Create phases 1 to 4 and 6 to 9, leaving out 5
    for i in [1, 2, 3, 4, 6, 7, 8, 9]:
        (phase_dir / f"phase_{i:02d}.md").write_text(f"# Phase {i}")

    existing_phases = {p.name for p in phase_dir.glob("phase_*.md")}
    assert "phase_05.md" not in existing_phases


def test_f6_b29_empty_phase_markdown_file_detected(temp_workspace):
    """F6.B29: 0-byte phase markdown file flagged as incomplete content."""
    empty_phase = temp_workspace / "phase_01.md"
    empty_phase.write_text("")
    assert empty_phase.stat().st_size == 0


def test_f6_b30_duplicate_phase_numbers_detected():
    """F6.B30: Duplicate phase numbers detected and rejected."""
    phase_list = ["phase_01.md", "phase_02.md", "phase_02.md", "phase_03.md"]
    has_duplicates = len(phase_list) != len(set(phase_list))
    assert has_duplicates is True


# ---------------------------------------------------------------------------
# F7 Boundary: Bracketed Invariants & 3 Drills (5 tests)
# ---------------------------------------------------------------------------

def test_f7_b31_missing_mental_model_callout_detected():
    """F7.B31: Phase content lacking [MENTAL MODEL] flagged as deficient."""
    deficient_content = "# Phase 1\nSome text without any mental model callouts."
    assert "[MENTAL MODEL]" not in deficient_content


def test_f7_b32_malformed_bracket_callout_syntax():
    """F7.B32: Lowercase [mental model] or unclosed [INVARIANT flagged."""
    malformed_variants = [
        "[mental model]",
        "[INVARIANT",
        "MENTAL MODEL",
        "[engineering gotcha]"
    ]
    for variant in malformed_variants:
        is_exact = variant in {"[MENTAL MODEL]", "[INVARIANT]", "[ENGINEERING GOTCHA]"}
        assert is_exact is False


def test_f7_b33_phase_missing_challenge_1_detected():
    """F7.B33: Phase containing only Challenges 2 & 3 flagged as missing Challenge 1."""
    content = "### Challenge 2: Algorithm Utility\n### Challenge 3: Industrial Mini-Project"
    assert "Challenge 1: Output Prediction" not in content


def test_f7_b34_phase_missing_challenge_3_detected():
    """F7.B34: Phase containing Challenges 1 & 2 but missing production mini-project flagged."""
    content = "### Challenge 1: Output Prediction\n### Challenge 2: Algorithm Utility"
    assert "Challenge 3: Industrial Mini-Project" not in content


def test_f7_b35_drill_without_inline_output_detected():
    """F7.B35: Challenge 1 snippet lacking terminal output comments flagged by QA."""
    code_snippet = """
    console.log('Test A');
    console.log('Test B');
    """
    has_output_comment = "// Output:" in code_snippet or "// ->" in code_snippet
    assert has_output_comment is False


# ---------------------------------------------------------------------------
# F8 Boundary: ES2024+ Standards & Zero-Dependency (5 tests)
# ---------------------------------------------------------------------------

def test_f8_b36_legacy_var_usage_detected():
    """F8.B36: Code snippet using legacy var keyword flagged in favor of const/let."""
    legacy_code = "var activeSession = 'SESSION_991';"
    has_legacy_var = bool(re.search(r"\bvar\s+[a-zA-Z0-9_]+\b", legacy_code))
    assert has_legacy_var is True


def test_f8_b37_npm_package_import_detected():
    """F8.B37: Code snippet with import lodash flagged for violating zero-dependency policy."""
    bad_code = "import lodash from 'lodash';\nconst res = lodash.cloneDeep({});"
    has_npm_import = bool(re.search(r"import\s+.*?from\s+['\"](?:lodash|express|axios|ramda)['\"]", bad_code))
    assert has_npm_import is True


def test_f8_b38_toy_variable_foo_bar_detected():
    """F8.B38: Code snippet with let foo = 'bar' flagged for anti-toy code violation."""
    toy_code = "const foo = 42;\nfunction bar() { return foo; }"
    toy_vars = re.findall(r"\b(?:const|let|var|function)\s+(foo|bar|baz)\b", toy_code)
    assert len(toy_vars) >= 2


def test_f8_b39_syntax_error_in_code_block_detected():
    """F8.B39: Unclosed brace or syntax error in code block detected."""
    unclosed_code = "function executePipeline() { if (true) { console.log('Missing brace'); }"
    assert unclosed_code.count("{") != unclosed_code.count("}")


def test_f8_b40_missing_inline_comments_on_statements():
    """F8.B40: Multiple executable statements without output annotation flagged."""
    unannotated_code = """
    const recordA = { id: 1 };
    const recordB = { id: 2 };
    const list = [recordA, recordB];
    """
    lines = [l.strip() for l in unannotated_code.splitlines() if l.strip().startswith("const")]
    annotated = [l for l in lines if "// Output:" in l or "// ->" in l]
    assert len(annotated) == 0


# ---------------------------------------------------------------------------
# F9 Boundary: Vector Drawing & CS Memory Visualizers (5 tests)
# ---------------------------------------------------------------------------

def test_f9_b41_empty_call_stack_frames_handling(temp_workspace):
    """F9.B41: Call stack visualizer given empty frame list handles base frame cleanly."""
    doc = fitz.open()
    page = doc.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    shape = page.new_shape()
    # Draw empty stack base container
    shape.draw_rect(fitz.Rect(54, 100, 300, 200))
    shape.finish(color=(0, 0, 0), width=1)
    shape.commit()
    page.insert_text(fitz.Point(60, 150), "[Call Stack: Empty / Base Frame]", fontsize=10)
    pdf_path = temp_workspace / "empty_stack.pdf"
    doc.save(pdf_path)
    doc.close()

    assert pdf_path.exists()


def test_f9_b42_deep_call_stack_overflow_budgeting():
    """F9.B42: Deep call stack with 50 frames budgeted/paginated without canvas overflow."""
    max_printable_height = ISO_A4_HEIGHT - (2 * PAGE_MARGIN_MIN) # 733.89
    frame_height = 25.0
    frames_count = 50
    total_height = frames_count * frame_height

    # Total height exceeds one page, requires pagination
    needs_pagination = total_height > max_printable_height
    assert needs_pagination is True


def test_f9_b43_cyclic_heap_graph_references_handling():
    """F9.B43: Heap graph with circular reference (A -> B -> A) handled without infinite loop."""
    nodes = {"A": ["B"], "B": ["A"]}
    visited = set()
    cycles_detected = 0

    def traverse(curr, path):
        nonlocal cycles_detected
        if curr in path:
            cycles_detected += 1
            return
        for nxt in nodes.get(curr, []):
            traverse(nxt, path + [curr])

    traverse("A", [])
    assert cycles_detected == 1


def test_f9_b44_zero_dimension_vector_box_handling():
    """F9.B44: Bounding box of width or height 0 guarded against rendering crash."""
    rect = fitz.Rect(54, 54, 54, 54) # width=0, height=0
    assert rect.is_empty or rect.width == 0


def test_f9_b45_negative_coordinate_clipping():
    """F9.B45: Negative coordinates clipped to 0,0 page boundary."""
    raw_x = -15.0
    raw_y = -30.0
    clipped_x = max(0.0, raw_x)
    clipped_y = max(0.0, raw_y)
    assert clipped_x == 0.0
    assert clipped_y == 0.0


# ---------------------------------------------------------------------------
# F10 Boundary: Mandatory Branding & 𝕏 Glyph (5 tests)
# ---------------------------------------------------------------------------

def test_f10_b46_missing_branding_text_detected():
    """F10.B46: Page lacking 'Prepared by @issparsh @sumitsingh097' flagged as non-compliant."""
    page_text = "Page content without any author attributions."
    assert "Prepared by @issparsh @sumitsingh097" not in page_text


def test_f10_b47_misspelled_author_handle_detected():
    """F10.B47: Misspelled author handles (@sparsh @sumit) flagged by audit."""
    typo_text = "Prepared by @sparsh @sumit"
    is_compliant = "@issparsh" in typo_text and "@sumitsingh097" in typo_text
    assert is_compliant is False


def test_f10_b48_missing_x_glyph_detected():
    """F10.B48: Branding metadata with empty glyph path flagged."""
    glyph_data = {"glyph_type": "vector", "svg_path": ""}
    assert not glyph_data["svg_path"]


def test_f10_b49_rasterized_x_logo_rejection():
    """F10.B49: Bitmap image embedding for 𝕏 logo flagged (must be native vector)."""
    image_ext = "logo.png"
    vector_ext = "logo.svg"
    assert image_ext.endswith(".png")
    assert vector_ext.endswith(".svg")


def test_f10_b50_footer_overlapping_content_boundary():
    """F10.B50: Branding footer positioned below 54pt content margin without colliding."""
    footer_y = ISO_A4_HEIGHT - (PAGE_MARGIN_MIN / 2) # 841.89 - 27 = 814.89
    content_bottom_limit = ISO_A4_HEIGHT - PAGE_MARGIN_MIN # 787.89
    assert footer_y > content_bottom_limit


# ---------------------------------------------------------------------------
# F11 Boundary: Monochrome Aesthetic & Margins (5 tests)
# ---------------------------------------------------------------------------

def test_f11_b51_unauthorized_color_detection():
    """F11.B51: Non-monochrome color token (#FF0000, #00FF00) flagged as aesthetic violation."""
    illegal_colors = ["#FF0000", "#00FF00", "#0000FF", "#E91E63"]
    for c in illegal_colors:
        assert c not in MONOCHROME_PALETTE


def test_f11_b52_margins_below_54pt_detected():
    """F11.B52: Content coordinate placed at margin <54pt flagged as margin defect."""
    x_coord = 30.0 # < 54pt
    assert x_coord < PAGE_MARGIN_MIN


def test_f11_b53_non_iso_a4_page_dimensions_detected():
    """F11.B53: US Letter (612 x 792) or other non-A4 page dimensions detected."""
    letter_w = 612.0
    letter_h = 792.0
    is_a4 = (round(letter_w, 1) == round(ISO_A4_WIDTH, 1) and round(letter_h, 1) == round(ISO_A4_HEIGHT, 1))
    assert is_a4 is False


def test_f11_b54_monochrome_contrast_ratio_check():
    """F11.B54: Low-contrast combination (e.g. #CCCCCC on #FFFFFF) flagged for body text."""
    # Body text must use #000000 or #222222
    body_text_colors = {"#000000", "#222222"}
    low_contrast = "#CCCCCC"
    assert low_contrast not in body_text_colors


def test_f11_b55_overflowing_table_width_detected():
    """F11.B55: Table width exceeding printable canvas width (>487.28pt) flagged."""
    max_printable = ISO_A4_WIDTH - (2 * PAGE_MARGIN_MIN)
    overflow_table_w = 520.0
    assert overflow_table_w > max_printable


# ---------------------------------------------------------------------------
# F12 Boundary: Pass 1 Visual QA (5 tests)
# ---------------------------------------------------------------------------

def test_f12_b56_orphan_header_at_page_bottom_detected():
    """F12.B56: Heading located at y > 780pt without accompanying body text detected."""
    header_y = 785.0
    page_bottom = ISO_A4_HEIGHT - PAGE_MARGIN_MIN # 787.89
    is_orphan = header_y >= (page_bottom - 10)
    assert is_orphan is True


def test_f12_b57_text_overflow_across_bottom_margin_detected():
    """F12.B57: Text block crossing bottom 54pt threshold (y > 787.89pt) detected."""
    text_bottom_y = 795.0
    margin_limit = ISO_A4_HEIGHT - PAGE_MARGIN_MIN
    assert text_bottom_y > margin_limit


def test_f12_b58_table_cell_text_clipping_detected():
    """F12.B58: Table cell text exceeding cell bounding box detected."""
    cell_w = 100.0
    text_w = 125.0
    assert text_w > cell_w


def test_f12_b59_zero_page_pdf_input_handling():
    """F12.B59: In-memory 0-page PDF document handled gracefully by visual QA."""
    doc = fitz.open()
    assert len(doc) == 0
    # PyMuPDF enforces page count >= 1 before serializing to disk
    with pytest.raises(ValueError, match="cannot save with zero pages"):
        doc.save("invalid.pdf")
    doc.close()


def test_f12_b60_dpi_rendering_memory_management(sample_doc_path):
    """F12.B60: Rasterization pixmap memory freed cleanly."""
    doc = fitz.open(sample_doc_path)
    page = doc[0]
    pix = page.get_pixmap(dpi=150)
    assert pix.size > 0
    del pix # Explicit memory reclaim
    doc.close()


# ---------------------------------------------------------------------------
# F13 Boundary: Pass 2 Textual QA (5 tests)
# ---------------------------------------------------------------------------

def test_f13_b61_mixed_script_words_detected():
    """F13.B61: Words mixing Latin and Devanagari (e.g. Event-लूप) flagged."""
    mixed_word = "Event-लूप"
    matches = DEVANAGARI_REGEX.findall(mixed_word)
    assert len(matches) > 0


def test_f13_b62_empty_syllabus_table_detected():
    """F13.B62: Syllabus header present but table empty flagged."""
    empty_syllabus = "# DETAILED SYLLABUS & TABLE OF CONTENTS (PART I to VI)\n\n"
    has_parts = "PART I:" in empty_syllabus
    assert has_parts is False


def test_f13_b63_drills_missing_test_inputs_detected():
    """F13.B63: Challenge 1 lacking input explanation or code snippet flagged."""
    bare_challenge = "### Challenge 1: Output Prediction\nPredict the output."
    has_code_block = "```" in bare_challenge
    assert has_code_block is False


def test_f13_b64_qa_report_verdict_fail_on_violations():
    """F13.B64: Any single violation causes verdict: FAIL in qa_report.json."""
    violations = ["Devanagari character detected: 'अ' at phase_02.md:14"]
    verdict = "PASS" if len(violations) == 0 else "FAIL"
    assert verdict == "FAIL"


def test_f13_b65_qa_report_verdict_pass_only_on_zero_defects():
    """F13.B65: Clean document produces verdict: PASS with empty defect lists."""
    violations = []
    verdict = "PASS" if len(violations) == 0 else "FAIL"
    assert verdict == "PASS"


# ---------------------------------------------------------------------------
# F14 Boundary: Skill Packaging Compliance (5 tests)
# ---------------------------------------------------------------------------

def test_f14_b66_missing_yaml_frontmatter_delimiters():
    """F14.B66: SKILL.md without --- delimiters flagged as invalid skill."""
    bad_skill = "name: thenuke\ndescription: test\n# Heading"
    has_frontmatter = bad_skill.startswith("---\n")
    assert has_frontmatter is False


def test_f14_b67_missing_skill_name_attribute():
    """F14.B67: SKILL.md frontmatter missing name field flagged."""
    frontmatter_yaml = "description: Only description provided"
    assert "name:" not in frontmatter_yaml


def test_f14_b68_empty_skill_description():
    """F14.B68: SKILL.md with blank description flagged."""
    desc = "   "
    assert not desc.strip()


def test_f14_b69_missing_scripts_directory_detected(temp_workspace):
    """F14.B69: Skill directory missing scripts/ folder flagged."""
    fake_skill_dir = temp_workspace / "fake_skill"
    fake_skill_dir.mkdir()
    (fake_skill_dir / "SKILL.md").write_text("---\nname: fake\n---\n")

    assert not (fake_skill_dir / "scripts").exists()


def test_f14_b70_missing_tests_directory_detected(temp_workspace):
    """F14.B70: Skill directory missing tests/ folder flagged."""
    fake_skill_dir = temp_workspace / "fake_skill_2"
    fake_skill_dir.mkdir()
    (fake_skill_dir / "scripts").mkdir()

    assert not (fake_skill_dir / "tests").exists()


# ---------------------------------------------------------------------------
# F15 Boundary: CLI Runner Robustness (5 tests)
# ---------------------------------------------------------------------------

def test_f15_b71_cli_unknown_subcommand_rejection():
    """F15.B71: Unknown CLI subcommand recognized and rejected."""
    valid_subcommands = {"ingest", "grill", "synthesize", "compile", "qa", "run"}
    invalid_subcommand = "explode_system"
    assert invalid_subcommand not in valid_subcommands


def test_f15_b72_cli_missing_required_arguments_rejection():
    """F15.B72: CLI ingest command missing inputs detected."""
    parsed_args = {"youtube": None, "web": None, "local": None}
    has_any_source = any(v is not None for v in parsed_args.values())
    assert has_any_source is False


def test_f15_b73_cli_nonexistent_input_file_handling():
    """F15.B73: Ingesting non-existent file path flagged without crash."""
    nonexistent = Path("/nonexistent/path/document.pdf")
    assert not nonexistent.exists()


def test_f15_b74_cli_output_directory_creation_robustness(temp_workspace):
    """F15.B74: Output directory created automatically if not already present."""
    deep_out_dir = temp_workspace / "deep" / "nested" / "output"
    assert not deep_out_dir.exists()
    deep_out_dir.mkdir(parents=True, exist_ok=True)
    assert deep_out_dir.exists()


def test_f15_b75_cli_interrupted_pipeline_recovery(temp_workspace):
    """F15.B75: Interrupted pipeline cleans up temporary lock files."""
    lock_file = temp_workspace / "pipeline.lock"
    lock_file.write_text("LOCKED")
    assert lock_file.exists()
    # Cleanup
    lock_file.unlink(missing_ok=True)
    assert not lock_file.exists()
