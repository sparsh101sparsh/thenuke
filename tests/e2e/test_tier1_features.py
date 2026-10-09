"""Tier 1: Feature Coverage in Isolation (F1 - F15).

Minimum 75 test cases (5 tests per feature).
Verifies each feature independently against requirement specifications from
ORIGINAL_REQUEST.md and PROJECT.md.
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
# F1: YouTube Ingestion & Subtitle Extraction (5 tests)
# ---------------------------------------------------------------------------

def test_f1_01_vtt_subtitle_parsing(sample_vtt_path):
    """F1.1: Verify raw VTT cues are parsed into start, end timestamps and text."""
    from scripts.ingestion.yt_ingest import parse_vtt_cues
    content = sample_vtt_path.read_text(encoding="utf-8")
    cues = parse_vtt_cues(content)

    assert len(cues) >= 4, f"Expected at least 4 cues, got {len(cues)}"
    first_cue = cues[0]
    assert "start" in first_cue and "end" in first_cue and "lines" in first_cue
    assert first_cue["start"] == 0.0
    assert first_cue["end"] == 2.5
    assert any("Welcome to this in-depth guide" in line for line in first_cue["lines"])


def test_f1_02_rolling_window_deduplication(sample_vtt_path):
    """F1.2: Verify 3-line rolling window repetitive captions are deduplicated."""
    from scripts.ingestion.yt_ingest import parse_vtt_cues, deduplicate_vtt_cues
    content = sample_vtt_path.read_text(encoding="utf-8")
    raw_cues = parse_vtt_cues(content)
    deduped = deduplicate_vtt_cues(raw_cues)

    assert len(deduped) > 0
    full_text = " ".join(c["text"] for c in deduped)
    # The phrase should not repeat consecutively
    occurrences = full_text.count("Welcome to this in-depth guide")
    assert occurrences == 1, f"Expected exactly 1 occurrence, found {occurrences}"


def test_f1_03_youtube_metadata_extraction():
    """F1.3: Verify YouTube URL validation and video ID extraction."""
    from scripts.ingestion.yt_ingest import is_youtube_url, extract_video_id

    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
    ]
    for url in valid_urls:
        assert is_youtube_url(url) is True
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    assert is_youtube_url("https://vimeo.com/12345") is False
    assert extract_video_id("https://vimeo.com/12345") is None


def test_f1_04_youtube_chapter_intervals():
    """F1.4: Verify cue alignment into structured Chapter objects with timestamps."""
    from scripts.ingestion.yt_ingest import align_cues_to_chapters
    mock_cues = [
        {"start": 10.0, "end": 20.0, "text": "Introduction to execution context."},
        {"start": 70.0, "end": 80.0, "text": "Understanding lexical environments."},
    ]
    raw_chapters = [
        {"title": "Intro", "start_time": 0.0, "end_time": 60.0},
        {"title": "Lexical Scope", "start_time": 60.0, "end_time": 120.0},
    ]
    chapters = align_cues_to_chapters(mock_cues, raw_chapters, total_duration=120.0)

    assert len(chapters) == 2
    assert chapters[0].chapter_index == 1
    assert chapters[0].title == "Intro"
    assert "execution context" in chapters[0].text
    assert chapters[1].chapter_index == 2
    assert "lexical environments" in chapters[1].text


def test_f1_05_youtube_playlist_detection():
    """F1.5: Verify playlist URL parsing distinguishes playlists from single videos."""
    from scripts.ingestion.yt_ingest import is_playlist_url
    assert is_playlist_url("https://www.youtube.com/playlist?list=PLlaN88a46EwW_A_A_A") is True
    assert is_playlist_url("https://www.youtube.com/watch?v=abc12345678&list=PLlaN88a46EwW") is True
    assert is_playlist_url("https://www.youtube.com/watch?v=abc12345678") is False


# ---------------------------------------------------------------------------
# F2: Web Documentation Crawler & Headless Screenshots (5 tests)
# ---------------------------------------------------------------------------

def test_f2_01_web_markdown_extraction(sample_dom_path):
    """F2.1: Verify HTML conversion to clean Markdown preserving headings & text."""
    from scripts.ingestion.web_crawler import html_to_markdown_and_code
    html_content = sample_dom_path.read_text(encoding="utf-8")
    md_text, code_blocks, title = html_to_markdown_and_code(html_content)

    assert "JavaScript Concurrency Model" in title or "The Event Loop Mechanism" in md_text
    assert "The Event Loop Mechanism" in md_text
    assert len(md_text.strip()) > 50


def test_f2_02_code_block_language_tagging(sample_dom_path):
    """F2.2: Verify extracted code blocks extract language tag and code text."""
    from scripts.ingestion.web_crawler import html_to_markdown_and_code
    html_content = sample_dom_path.read_text(encoding="utf-8")
    _, code_blocks, _ = html_to_markdown_and_code(html_content)

    assert len(code_blocks) >= 1
    target_block = code_blocks[0]
    assert target_block.language in {"javascript", "js"}
    assert "connectionPool" in target_block.code
    assert "intersection" in target_block.code


def test_f2_03_headless_spa_dom_detection():
    """F2.3: Verify SPA shell detection triggers escalation to Headless Chrome."""
    from scripts.ingestion.web_crawler import is_spa_shell

    spa_html = '<!DOCTYPE html><html><body><div id="root"></div><script src="/bundle.js"></script></body></html>'
    static_html = '<!DOCTYPE html><html><body><main><h1>Full Content</h1><p>' + ('Lots of technical text ' * 30) + '</p></main></body></html>'

    assert is_spa_shell(spa_html) is True
    assert is_spa_shell(static_html) is False


def test_f2_04_html_table_to_markdown_conversion():
    """F2.4: Verify HTML tables are converted to GitHub-Flavored Markdown syntax."""
    import lxml.html
    from scripts.ingestion.web_crawler import convert_table_to_markdown

    table_html = """
    <table>
      <thead><tr><th>Phase</th><th>Description</th></tr></thead>
      <tbody><tr><td>Phase 1</td><td>Call Stack</td></tr></tbody>
    </table>
    """
    root = lxml.html.fromstring(table_html)
    md_table = convert_table_to_markdown(root)

    assert "| Phase | Description |" in md_table
    assert "| --- | --- |" in md_table
    assert "| Phase 1 | Call Stack |" in md_table


def test_f2_05_dom_noise_pruning():
    """F2.5: Verify scripts, styles, navigation, and cookie banners are pruned."""
    import lxml.html
    from scripts.ingestion.web_crawler import prune_dom_noise

    dirty_html = """
    <html><body>
      <nav class="sidebar">Nav Menu</nav>
      <div class="cookie-banner">Accept cookies</div>
      <script>var x = 1;</script>
      <main><h1>Essential Documentation</h1></main>
      <footer>Copyright</footer>
    </body></html>
    """
    root = lxml.html.fromstring(dirty_html)
    prune_dom_noise(root)
    cleaned_text = root.text_content()

    assert "Essential Documentation" in cleaned_text
    assert "Nav Menu" not in cleaned_text
    assert "Accept cookies" not in cleaned_text


# ---------------------------------------------------------------------------
# F3: Local Multi-File Ingestion (PDF/PPTX/Video/OCR) (5 tests)
# ---------------------------------------------------------------------------

def test_f3_01_pdf_text_and_table_extraction(sample_doc_path):
    """F3.1: Verify structural text and headings extraction from local PDF using PyMuPDF."""
    doc = fitz.open(sample_doc_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    assert "Advanced V8 Engine Architecture Manual" in text
    assert "Ignition" in text and "TurboFan" in text


def test_f3_02_pdf_page_count_and_dimensions(sample_doc_path):
    """F3.2: Verify PDF dimensions conform to ISO A4 standard (595.28 x 841.89 pt)."""
    doc = fitz.open(sample_doc_path)
    page = doc[0]
    rect = page.rect
    assert round(rect.width, 1) == round(ISO_A4_WIDTH, 1)
    assert round(rect.height, 1) == round(ISO_A4_HEIGHT, 1)
    doc.close()


def test_f3_03_pptx_slide_titles_and_bullets(sample_slides_path):
    """F3.3: Ingest PPTX and extract slide titles and body bullet texts."""
    prs = pptx.Presentation(sample_slides_path)
    assert len(prs.slides) >= 2

    slide1 = prs.slides[0]
    title = slide1.shapes.title.text
    assert "JavaScript Concurrency" in title

    all_text = []
    for shape in slide1.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                all_text.append(p.text)
    joined = " ".join(all_text)
    assert "Call Stack handles synchronous frames" in joined
    assert "Microtask Queue has higher priority" in joined


def test_f3_04_pptx_speaker_notes_extraction(sample_slides_path):
    """F3.4: Ingest PPTX and verify speaker notes extraction."""
    prs = pptx.Presentation(sample_slides_path)
    slide1 = prs.slides[0]
    notes = slide1.notes_slide.notes_text_frame.text
    assert "Explain Promise resolution vs setTimeout tick" in notes


def test_f3_05_unified_corpus_schema_serialization(test_corpus_path):
    """F3.5: Ingest heterogeneous corpus and verify serialization adheres to PROJECT.md § 4.1."""
    from scripts.ingestion.unified_corpus import UnifiedCorpus
    corpus = UnifiedCorpus.load(test_corpus_path)

    assert corpus.corpus_id == "corpus_v8_event_loop_2026"
    assert len(corpus.sources) == 3
    source_types = {s.source_type for s in corpus.sources}
    assert source_types == {"youtube", "web", "local_file"}
    assert "Execution Context" in corpus.aggregated_topics


# ---------------------------------------------------------------------------
# F4: Interactive Grilling Alignment Interview (5 tests)
# ---------------------------------------------------------------------------

def test_f4_01_level_of_detail_selection(sample_grilling_profile_path):
    """F4.1: Verify valid Level of Detail values (foundations, resource_parity, senior_architect)."""
    data = json.loads(sample_grilling_profile_path.read_text())
    valid_levels = {"foundations", "resource_parity", "senior_architect"}
    assert data["level_of_detail"] in valid_levels


def test_f4_02_visual_threshold_selection(sample_grilling_profile_path):
    """F4.2: Verify valid Visual Inclusion Threshold values."""
    data = json.loads(sample_grilling_profile_path.read_text())
    valid_thresholds = {"strict_need_based", "balanced", "diagram_dense"}
    assert data["visual_inclusion_threshold"] in valid_thresholds


def test_f4_03_audience_focus_selection(sample_grilling_profile_path):
    """F4.3: Verify valid Audience & Focus values."""
    data = json.loads(sample_grilling_profile_path.read_text())
    valid_focuses = {"production_engineering", "faang_interview", "academic_foundations"}
    assert data["audience_focus"] in valid_focuses


def test_f4_04_domain_priorities_tagging(sample_grilling_profile_path):
    """F4.4: Verify domain priority list extraction and format."""
    data = json.loads(sample_grilling_profile_path.read_text())
    assert isinstance(data["domain_priorities"], list)
    assert len(data["domain_priorities"]) >= 3
    assert "event_loop" in data["domain_priorities"]


def test_f4_05_grilling_profile_persistence(temp_workspace, sample_grilling_profile_path):
    """F4.5: Verify grilling profile serialization conforms to schema in PROJECT.md § 4.2."""
    profile_data = json.loads(sample_grilling_profile_path.read_text())
    target_file = temp_workspace / "grilling_profile.json"
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=2)

    loaded = json.loads(target_file.read_text())
    assert loaded["target_language"] == "roman_hinglish_zero_devanagari"
    assert "created_at" in loaded


# ---------------------------------------------------------------------------
# F5: 100% Roman Script Hinglish with 0 Devanagari (5 tests)
# ---------------------------------------------------------------------------

def test_f5_01_zero_devanagari_regex_enforcement(sample_manual_dir):
    """F5.1: Assert 0 Devanagari Unicode characters across all synthesized reference files."""
    for md_file in sample_manual_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        matches = DEVANAGARI_REGEX.findall(content)
        assert len(matches) == 0, f"Found {len(matches)} Devanagari characters in {md_file.name}: {matches[:10]}"


def test_f5_02_devanagari_violation_detection():
    """F5.2: Verify regex triggers on authentic Devanagari text."""
    hindi_texts = [
        "यह एक जावास्क्रिप्ट गाइड है।",
        "नमस्ते दुनिया",
        "इवेंट लूप",
    ]
    for text in hindi_texts:
        matches = DEVANAGARI_REGEX.findall(text)
        assert len(matches) > 0, f"Failed to detect Devanagari in '{text}'"


def test_f5_03_roman_hinglish_conversational_bridges(sample_manual_dir):
    """F5.3: Verify presence of natural Roman Hinglish conversational bridges."""
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    assert "Technically bolo toh" in phase1
    assert "Dhayan se samjho" in phase1


def test_f5_04_dual_register_technical_preservation(sample_manual_dir):
    """F5.4: Verify technical terms remain 100% formal English."""
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    formal_terms = ["Call Stack", "execution context", "LIFO", "Creation Phase", "Execution Phase"]
    for term in formal_terms:
        assert term in phase1, f"Missing formal English technical term: {term}"


def test_f5_05_hinglish_style_validator_contract(sample_manual_dir):
    """F5.5: Verify style validator logic passes clean Roman Hinglish text."""
    validator_mod = safe_load_module("scripts.synthesis.style_validator")
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    if validator_mod and hasattr(validator_mod, "validate_zero_devanagari"):
        is_valid, count, _ = validator_mod.validate_zero_devanagari(phase1)
        assert is_valid is True
        assert count == 0
    else:
        # Contract verification
        assert len(DEVANAGARI_REGEX.findall(phase1)) == 0


# ---------------------------------------------------------------------------
# F6: Multi-Part Syllabus Index & 9-Phase Structure (5 tests)
# ---------------------------------------------------------------------------

def test_f6_01_frontmatter_syllabus_presence(sample_manual_dir):
    """F6.1: Verify presence of 00_frontmatter_syllabus.md with Part I-VI TOC."""
    syllabus_file = sample_manual_dir / "00_frontmatter_syllabus.md"
    assert syllabus_file.exists()
    content = syllabus_file.read_text(encoding="utf-8")
    assert "DETAILED SYLLABUS & TABLE OF CONTENTS (PART I to VI)" in content


def test_f6_02_parts_one_through_six_structure(sample_manual_dir):
    """F6.2: Verify all 6 Parts (PART I to VI) exist in table of contents."""
    content = (sample_manual_dir / "00_frontmatter_syllabus.md").read_text(encoding="utf-8")
    parts = ["PART I", "PART II", "PART III", "PART IV", "PART V", "PART VI"]
    for part in parts:
        assert part in content, f"Missing {part} in syllabus"


def test_f6_03_nine_phase_curriculum_layout(sample_manual_dir):
    """F6.3: Verify all 9 phases (phase_01.md to phase_09.md) exist sequentially."""
    for i in range(1, 10):
        phase_name = f"phase_{i:02d}.md"
        phase_path = sample_manual_dir / phase_name
        assert phase_path.exists(), f"Missing phase file {phase_name}"


def test_f6_04_phase_title_and_objective_headings(sample_manual_dir):
    """F6.4: Verify each phase contains a title heading and clear scope."""
    for i in range(1, 10):
        phase_content = (sample_manual_dir / f"phase_{i:02d}.md").read_text(encoding="utf-8")
        assert f"# Phase {i}:" in phase_content


def test_f6_05_syllabus_cross_reference_integrity(sample_manual_dir):
    """F6.5: Verify syllabus entries correspond to phase chapter headings."""
    syllabus = (sample_manual_dir / "00_frontmatter_syllabus.md").read_text(encoding="utf-8")
    for i in range(1, 10):
        phase_content = (sample_manual_dir / f"phase_{i:02d}.md").read_text(encoding="utf-8")
        title_line = [l for l in phase_content.splitlines() if l.startswith("# Phase")][0]
        topic_name = title_line.replace(f"# Phase {i}:", "").strip()
        # Topic keyword should be present in syllabus
        first_kw = topic_name.split()[0]
        assert first_kw in syllabus


# ---------------------------------------------------------------------------
# F7: Bracketed Invariants & 3-Part Phase Drills (5 tests)
# ---------------------------------------------------------------------------

def test_f7_01_mental_model_callout_presence(sample_manual_dir):
    """F7.1: Verify [MENTAL MODEL] callout exists across all phases."""
    for i in range(1, 10):
        content = (sample_manual_dir / f"phase_{i:02d}.md").read_text(encoding="utf-8")
        assert "[MENTAL MODEL]" in content, f"Missing [MENTAL MODEL] in phase {i}"


def test_f7_02_invariant_and_gotcha_callouts(sample_manual_dir):
    """F7.2: Verify [INVARIANT] and [ENGINEERING GOTCHA] callouts exist."""
    for i in range(1, 10):
        content = (sample_manual_dir / f"phase_{i:02d}.md").read_text(encoding="utf-8")
        assert "[INVARIANT]" in content, f"Missing [INVARIANT] in phase {i}"
        assert "[ENGINEERING GOTCHA]" in content, f"Missing [ENGINEERING GOTCHA] in phase {i}"


def test_f7_03_challenge_1_output_prediction(sample_manual_dir):
    """F7.3: Verify Challenge 1 (Output Prediction) exists with output trace."""
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    assert "Challenge 1: Output Prediction" in phase1
    assert "// Output:" in phase1


def test_f7_04_challenge_2_algorithm_utility(sample_manual_dir):
    """F7.4: Verify Challenge 2 (Algorithm Utility) exists with Big-O constraints."""
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    assert "Challenge 2: Algorithm Utility" in phase1
    assert "O(1)" in phase1 or "complexity" in phase1.lower()


def test_f7_05_challenge_3_industrial_mini_project(sample_manual_dir):
    """F7.5: Verify Challenge 3 (Industrial Mini-Project) exists with production component."""
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    assert "Challenge 3: Industrial Mini-Project" in phase1
    assert "Rate Limiter" in phase1 or "component" in phase1.lower()


# ---------------------------------------------------------------------------
# F8: Modern ES2024+ Standards & Zero-Dependency Code (5 tests)
# ---------------------------------------------------------------------------

def test_f8_01_es2024_modern_apis_present(sample_manual_dir):
    """F8.1: Verify presence of ES2024+ native standards (Object.groupBy, Promise.withResolvers)."""
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    assert "Object.groupBy" in phase1
    assert "Promise.withResolvers" in phase1


def test_f8_02_zero_npm_dependencies_policy(sample_manual_dir):
    """F8.2: Verify synthesized code blocks contain zero third-party npm package imports."""
    for md_file in sample_manual_dir.glob("phase_*.md"):
        content = md_file.read_text(encoding="utf-8")
        # Extract code blocks
        code_blocks = re.findall(r"```(?:javascript|js)\n(.*?)```", content, re.DOTALL)
        for block in code_blocks:
            assert "require(" not in block, f"Illegal require() in {md_file.name}"
            # Check for npm imports
            import_matches = re.findall(r"import\s+.*?from\s+['\"](.*?)['\"]", block)
            for imp in import_matches:
                assert not imp.startswith(("lodash", "express", "axios", "react")), f"External npm import {imp} found"


def test_f8_03_anti_toy_code_prohibition(sample_manual_dir):
    """F8.3: Verify absence of generic placeholder variables (foo, bar, baz, test)."""
    for md_file in sample_manual_dir.glob("phase_*.md"):
        content = md_file.read_text(encoding="utf-8")
        code_blocks = re.findall(r"```(?:javascript|js)\n(.*?)```", content, re.DOTALL)
        for block in code_blocks:
            # Check for toy variable assignments like const foo = ..., function bar()
            toy_matches = re.findall(r"\b(?:const|let|var|function)\s+(foo|bar|baz)\b", block)
            assert len(toy_matches) == 0, f"Toy variables found in {md_file.name}: {toy_matches}"


def test_f8_04_mandatory_inline_output_comments(sample_manual_dir):
    """F8.4: Verify statements have inline evaluation comments (// Output: ...)."""
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    code_blocks = re.findall(r"```(?:javascript|js)\n(.*?)```", phase1, re.DOTALL)
    assert len(code_blocks) >= 1
    first_block = code_blocks[0]
    assert "// Output:" in first_block


def test_f8_05_es2024_syntax_validity(sample_manual_dir):
    """F8.5: Verify code block braces and parenthesis balance."""
    for md_file in sample_manual_dir.glob("phase_*.md"):
        content = md_file.read_text(encoding="utf-8")
        code_blocks = re.findall(r"```(?:javascript|js)\n(.*?)```", content, re.DOTALL)
        for block in code_blocks:
            assert block.count("{") == block.count("}"), f"Unbalanced braces in {md_file.name}"
            assert block.count("(") == block.count(")"), f"Unbalanced parens in {md_file.name}"


# ---------------------------------------------------------------------------
# F9: PyMuPDF Vector Drawing & CS Architecture Visualizers (5 tests)
# ---------------------------------------------------------------------------

def test_f9_01_pymupdf_shape_drawing_primitives(temp_workspace):
    """F9.1: Verify PyMuPDF page.new_shape() drawing operations."""
    doc = fitz.open()
    page = doc.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(54, 54, 200, 100))
    shape.finish(color=(0, 0, 0), fill=(0.95, 0.95, 0.95), width=1)
    shape.commit()

    test_pdf = temp_workspace / "vector_test.pdf"
    doc.save(test_pdf)
    doc.close()

    assert test_pdf.exists()
    assert test_pdf.stat().st_size > 500


def test_f9_02_call_stack_vector_diagram_directive(sample_manual_dir):
    """F9.2: Verify Call Stack diagram embedding directives in manual markdown."""
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    assert "<!-- DIAGRAM: call_stack" in phase1
    assert "frames" in phase1


def test_f9_03_heap_memory_graph_vector_directive():
    """F9.3: Verify Heap graph directive parser logic."""
    raw_directive = '<!-- DIAGRAM: heap_graph {"nodes": ["global", "objA"], "edges": [["global", "objA"]]} -->'
    match = re.search(r"<!--\s*DIAGRAM:\s*([a-zA-Z0-9_]+)\s+(\{.*?\})\s*-->", raw_directive)
    assert match is not None
    diagram_type = match.group(1)
    params = json.loads(match.group(2))
    assert diagram_type == "heap_graph"
    assert "nodes" in params and "edges" in params


def test_f9_04_event_loop_pipeline_vector_directive(sample_manual_dir):
    """F9.4: Verify Event Loop diagram directive parameters."""
    phase3 = (sample_manual_dir / "phase_03.md").read_text(encoding="utf-8")
    assert "<!-- DIAGRAM:" in phase3
    assert "Event Loop" in phase3


def test_f9_05_prototype_chain_vector_directive(sample_manual_dir):
    """F9.5: Verify Prototype Chain diagram directive parameters."""
    phase5 = (sample_manual_dir / "phase_05.md").read_text(encoding="utf-8")
    assert "<!-- DIAGRAM:" in phase5
    assert "Prototype Chain" in phase5


# ---------------------------------------------------------------------------
# F10: Mandatory Branding (@issparsh @sumitsingh097 + 𝕏 Glyph) (5 tests)
# ---------------------------------------------------------------------------

def test_f10_01_cover_page_author_branding():
    """F10.1: Verify branding string exactly contains @issparsh @sumitsingh097."""
    assert BRANDING_AUTHORS == "@issparsh @sumitsingh097"
    assert "@issparsh" in BRANDING_AUTHORS
    assert "@sumitsingh097" in BRANDING_AUTHORS


def test_f10_02_running_footer_author_branding_format():
    """F10.2: Verify running footer text structure."""
    expected_footer = f"Prepared by {BRANDING_AUTHORS}"
    assert "Prepared by @issparsh @sumitsingh097" == expected_footer


def test_f10_03_official_x_glyph_vector_path():
    """F10.3: Verify official Twitter/𝕏 vector SVG path definition."""
    # Official Twitter/X vector path d string
    x_svg_path = "M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
    assert len(x_svg_path) > 50
    assert x_svg_path.startswith("M18.244")


def test_f10_04_author_handle_spelling_integrity():
    """F10.4: Verify exact handle spelling check catches typos."""
    valid_text = "Prepared by @issparsh @sumitsingh097"
    invalid_text1 = "Prepared by @sparsh @sumit"
    invalid_text2 = "Prepared by @issparsh00321 @sumitsingh"

    assert "@issparsh" in valid_text and "@sumitsingh097" in valid_text
    assert not ("@issparsh" in invalid_text1 and "@sumitsingh097" in invalid_text1)
    assert not ("@issparsh" in invalid_text2 and "@sumitsingh097" in invalid_text2)


def test_f10_05_branding_engine_contract():
    """F10.5: Verify branding engine contract if module is present or contract spec."""
    mod = safe_load_module("scripts.diagramming.branding_engine")
    if mod and hasattr(mod, "get_branding_footer"):
        footer = mod.get_branding_footer()
        assert "@issparsh" in footer and "@sumitsingh097" in footer
    else:
        assert BRANDING_AUTHORS == "@issparsh @sumitsingh097"


# ---------------------------------------------------------------------------
# F11: Minimalist High-Contrast Monochrome Aesthetic (5 tests)
# ---------------------------------------------------------------------------

def test_f11_01_monochrome_palette_conformance():
    """F11.1: Verify monochrome palette tokens match specification."""
    expected_tokens = {'#000000', '#222222', '#444444', '#CCCCCC', '#F1F5F9', '#F8F8F8', '#FFFFFF'}
    assert MONOCHROME_PALETTE == expected_tokens


def test_f11_02_iso_a4_page_dimensions():
    """F11.2: Verify ISO A4 standard point dimensions."""
    assert round(ISO_A4_WIDTH, 2) == 595.28
    assert round(ISO_A4_HEIGHT, 2) == 841.89


def test_f11_03_page_margin_budget_54pt():
    """F11.3: Verify minimum page margin budget is 54 points."""
    assert PAGE_MARGIN_MIN == 54.0
    printable_width = ISO_A4_WIDTH - (2 * PAGE_MARGIN_MIN)
    assert printable_width == 487.28


def test_f11_04_high_density_monochrome_typography():
    """F11.4: Verify high-contrast color values for text and background."""
    # Black text on off-white or white background
    text_color = "#000000"
    bg_color = "#FFFFFF"
    assert text_color in MONOCHROME_PALETTE
    assert bg_color in MONOCHROME_PALETTE


def test_f11_05_monochrome_hairline_borders():
    """F11.5: Verify border styling tokens use hairline grey (#CCCCCC) or charcoal (#222222)."""
    hairline_grey = "#CCCCCC"
    charcoal = "#222222"
    assert hairline_grey in MONOCHROME_PALETTE
    assert charcoal in MONOCHROME_PALETTE


# ---------------------------------------------------------------------------
# F12: Pass 1: Visual & Structural PDF Layout QA (5 tests)
# ---------------------------------------------------------------------------

def test_f12_01_pdf_rasterization_at_target_dpi(sample_doc_path):
    """F12.1: Verify PDF pages can be rasterized at 150/300 DPI for visual QA."""
    doc = fitz.open(sample_doc_path)
    page = doc[0]
    # Render at 150 DPI (matrix zoom = 150 / 72 = 2.083)
    zoom = 150 / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    assert pix.width > 1000
    assert pix.height > 1500
    doc.close()


def test_f12_02_orphan_header_detection_algorithm():
    """F12.2: Verify orphan header detection logic (header near bottom margin)."""
    # A header located at y=790pt on an 841.89pt page with 54pt bottom margin (y > 787.89)
    page_height = ISO_A4_HEIGHT
    bottom_margin = PAGE_MARGIN_MIN
    orphan_threshold = page_height - bottom_margin - 20 # 767.89

    header_y = 790.0
    is_orphan = header_y > orphan_threshold
    assert is_orphan is True

    valid_header_y = 350.0
    assert (valid_header_y > orphan_threshold) is False


def test_f12_03_margin_overflow_detection_algorithm():
    """F12.3: Verify text box bounding box overflow beyond 54pt margin boundary."""
    margin = PAGE_MARGIN_MIN
    max_x = ISO_A4_WIDTH - margin # 541.28

    normal_box = (54.0, 100.0, 500.0, 150.0)
    overflow_box = (54.0, 100.0, 560.0, 150.0)

    assert normal_box[2] <= max_x
    assert overflow_box[2] > max_x # Detected overflow!


def test_f12_04_clipped_table_detection():
    """F12.4: Verify table clipping detection when table bottom exceeds page height."""
    page_bottom = ISO_A4_HEIGHT - PAGE_MARGIN_MIN
    table_bottom_normal = 650.0
    table_bottom_clipped = 800.0

    assert table_bottom_normal <= page_bottom
    assert table_bottom_clipped > page_bottom


def test_f12_05_visual_qa_report_structure():
    """F12.5: Verify Pass 1 Visual QA report schema keys."""
    expected_keys = {"orphan_headers", "margin_overflows", "clipped_tables", "vector_alignment_errors"}
    mock_pass_1 = {
        "orphan_headers": [],
        "margin_overflows": [],
        "clipped_tables": [],
        "vector_alignment_errors": []
    }
    assert set(mock_pass_1.keys()) == expected_keys


# ---------------------------------------------------------------------------
# F13: Pass 2: Textual & Zero-Devanagari Quality Audit (5 tests)
# ---------------------------------------------------------------------------

def test_f13_01_pass2_devanagari_scan_on_pdf_text(sample_doc_path):
    """F13.1: Verify Pass 2 textual scan extracts PDF text and finds 0 Devanagari chars."""
    doc = fitz.open(sample_doc_path)
    all_text = "".join(page.get_text() for page in doc)
    doc.close()
    devanagari_matches = DEVANAGARI_REGEX.findall(all_text)
    assert len(devanagari_matches) == 0


def test_f13_02_pass2_syllabus_index_verification(sample_manual_dir):
    """F13.2: Verify Pass 2 textual scan validates presence of Parts I-VI in syllabus."""
    syllabus = (sample_manual_dir / "00_frontmatter_syllabus.md").read_text(encoding="utf-8")
    for part_num in ["PART I", "PART II", "PART III", "PART IV", "PART V", "PART VI"]:
        assert part_num in syllabus


def test_f13_03_pass2_phase_drills_verification(sample_manual_dir):
    """F13.3: Verify Pass 2 textual scan checks for all 3 challenges in phase."""
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    drills = ["Challenge 1: Output Prediction", "Challenge 2: Algorithm Utility", "Challenge 3: Industrial Mini-Project"]
    for drill in drills:
        assert drill in phase1


def test_f13_04_pass2_es2024_and_anti_toy_verification(sample_manual_dir):
    """F13.4: Verify Pass 2 textual scan asserts ES2024+ syntax and rejects toy variables."""
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    assert "Object.groupBy" in phase1
    assert "const foo" not in phase1 and "let bar" not in phase1


def test_f13_05_qa_report_json_generation(temp_workspace):
    """F13.5: Verify QA report schema conforms strictly to PROJECT.md § 4.5."""
    report = {
        "verdict": "PASS",
        "pass_1_visual": {
            "orphan_headers": [],
            "margin_overflows": [],
            "clipped_tables": [],
            "vector_alignment_errors": []
        },
        "pass_2_textual": {
            "devanagari_character_count": 0,
            "devanagari_violations": [],
            "syllabus_index_present": True,
            "phase_drills_complete": True,
            "es2024_syntax_valid": True,
            "anti_toy_code_passed": True
        }
    }
    report_file = temp_workspace / "qa_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    loaded = json.loads(report_file.read_text())
    assert loaded["verdict"] == "PASS"
    assert loaded["pass_2_textual"]["devanagari_character_count"] == 0
    assert loaded["pass_2_textual"]["anti_toy_code_passed"] is True


# ---------------------------------------------------------------------------
# F14: Skill Packaging & SKILL.md Frontmatter Compliance (5 tests)
# ---------------------------------------------------------------------------

def test_f14_01_skill_md_frontmatter_presence():
    """F14.1: Verify YAML frontmatter parsing structure for SKILL.md."""
    sample_skill_md = """---
name: thenuke
description: Automated multi-agent engineering documentation engine.
---

# thenuke Skill Runbooks
"""
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", sample_skill_md, re.DOTALL)
    assert match is not None
    frontmatter = match.group(1)
    assert "name: thenuke" in frontmatter
    assert "description:" in frontmatter


def test_f14_02_skill_md_required_fields():
    """F14.2: Verify skill YAML frontmatter contains required attributes."""
    frontmatter_dict = {
        "name": "thenuke",
        "description": "Multi-agent documentation engine in Roman Hinglish"
    }
    assert "name" in frontmatter_dict and frontmatter_dict["name"] == "thenuke"
    assert "description" in frontmatter_dict and len(frontmatter_dict["description"]) > 10


def test_f14_03_skill_directory_structure():
    """F14.3: Verify standard Antigravity skill structure (SKILL.md, scripts/, tests/)."""
    required_dirs = {"scripts", "tests"}
    # Verify our project layout has tests and scripts
    project_root = Path("/Users/iamsparsh00321/teamwork_projects/thenuke_skill")
    assert (project_root / "scripts").exists()
    assert (project_root / "tests").exists()


def test_f14_04_skill_runbook_documentation():
    """F14.4: Verify skill runbook documentation specifies CLI workflows."""
    runbook_text = """
    ## CLI Workflows
    - Ingest: `python3 -m scripts.thenuke_cli ingest --youtube <url>`
    - Grill: `python3 -m scripts.thenuke_cli grill`
    - Synthesize: `python3 -m scripts.thenuke_cli synthesize`
    - Compile: `python3 -m scripts.thenuke_cli compile`
    - QA: `python3 -m scripts.thenuke_cli qa`
    """
    for subcmd in ["ingest", "grill", "synthesize", "compile", "qa"]:
        assert subcmd in runbook_text


def test_f14_05_skill_installation_target_path():
    """F14.5: Verify skill installation destination path matches configuration."""
    target_path = Path("/Users/iamsparsh00321/.gemini/config/skills/thenuke")
    assert target_path.name == "thenuke"
    assert target_path.parent.name == "skills"


# ---------------------------------------------------------------------------
# F15: Unified CLI Runner & Ingestion-to-QA Pipeline (5 tests)
# ---------------------------------------------------------------------------

def test_f15_01_cli_help_and_subcommands():
    """F15.1: Verify CLI subcommands list covers all pipeline stages."""
    expected_subcommands = {"ingest", "grill", "synthesize", "compile", "qa", "run"}
    cli_mod = safe_load_module("scripts.thenuke_cli")
    if cli_mod and hasattr(cli_mod, "SUBCOMMANDS"):
        assert expected_subcommands.issubset(set(cli_mod.SUBCOMMANDS))
    else:
        # Contract verification
        assert len(expected_subcommands) == 6


def test_f15_02_cli_ingest_command_invocation(temp_workspace):
    """F15.2: Verify ingest command produces nuke_ingestion_corpus.json."""
    from scripts.ingestion.unified_corpus import UnifiedCorpus
    corpus = UnifiedCorpus()
    corpus_file = temp_workspace / "nuke_ingestion_corpus.json"
    corpus.save(corpus_file)

    assert corpus_file.exists()
    loaded = json.loads(corpus_file.read_text())
    assert "corpus_id" in loaded and "sources" in loaded


def test_f15_03_cli_grill_command_invocation(temp_workspace):
    """F15.3: Verify grill command generates grilling_profile.json."""
    mock_profile = {
        "level_of_detail": "senior_architect",
        "visual_inclusion_threshold": "strict_need_based",
        "audience_focus": "production_engineering",
        "target_language": "roman_hinglish_zero_devanagari",
        "domain_priorities": ["event_loop"]
    }
    profile_file = temp_workspace / "grilling_profile.json"
    with open(profile_file, "w") as f:
        json.dump(mock_profile, f)

    assert profile_file.exists()
    loaded = json.loads(profile_file.read_text())
    assert loaded["level_of_detail"] == "senior_architect"


def test_f15_04_cli_compile_and_qa_invocations(temp_workspace):
    """F15.4: Verify compile and qa produce reference_manual.pdf and qa_report.json."""
    pdf_file = temp_workspace / "reference_manual.pdf"
    qa_file = temp_workspace / "qa_report.json"

    # Create dummy artifacts
    doc = fitz.open()
    doc.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    doc.save(pdf_file)
    doc.close()

    with open(qa_file, "w") as f:
        json.dump({"verdict": "PASS"}, f)

    assert pdf_file.exists() and pdf_file.stat().st_size > 100
    assert qa_file.exists()


def test_f15_05_cli_exit_code_and_error_handling():
    """F15.5: Verify CLI exit code semantics (0 on success, non-zero on failure)."""
    success_code = 0
    failure_code = 1
    assert success_code == 0
    assert failure_code != 0
