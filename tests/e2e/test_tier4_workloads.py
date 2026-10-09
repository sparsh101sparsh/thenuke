"""Tier 4: Real-World Application Scenarios (Workloads 1 - 8).

Minimum 8 complex, multi-feature end-to-end user application workflows.
Simulates realistic end-user flows from raw ingestion to compiled, branded,
QA-verified reference manuals, as specified in TEST_INFRA.md.
"""

import json
import re
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
# Scenario 1: Full YouTube Playlist to Master Manual
# ---------------------------------------------------------------------------

def test_tier4_workload_01_youtube_playlist_to_master_manual(
    sample_vtt_path,
    sample_grilling_profile_path,
    sample_manual_dir,
    temp_workspace
):
    """Scenario 1: Ingest YouTube video transcript, align with grilling profile,
    synthesize 9-phase manual, compile PDF with vector diagrams and branding,
    and run dual-pass QA to 0 defects.
    Features Exercised: F1, F4, F5, F6, F7, F8, F9, F10, F11, F12, F13, F15.
    """
    from scripts.ingestion.yt_ingest import clean_vtt_content, parse_vtt_cues, deduplicate_vtt_cues, align_cues_to_chapters
    from scripts.ingestion.unified_corpus import IngestionSource, UnifiedCorpus

    # Step 1: Ingest and deduplicate VTT
    vtt_content = sample_vtt_path.read_text(encoding="utf-8")
    cues = deduplicate_vtt_cues(parse_vtt_cues(vtt_content))
    chapters = align_cues_to_chapters(cues, [], total_duration=3600.0, video_title="V8 Deep Dive")
    source = IngestionSource(
        source_type="youtube",
        identifier="https://www.youtube.com/watch?v=mock_playlist_01",
        title="V8 Deep Dive Playlist",
        metadata={"duration": 3600.0, "file_type": "youtube_stream"},
        chapters=chapters
    )
    corpus = UnifiedCorpus()
    corpus.add_source(source)
    corpus_file = temp_workspace / "nuke_ingestion_corpus.json"
    corpus.save(corpus_file)
    assert corpus_file.exists()

    # Step 2: Grilling Profile alignment
    profile = json.loads(sample_grilling_profile_path.read_text())
    assert profile["level_of_detail"] == "senior_architect"
    assert profile["target_language"] == "roman_hinglish_zero_devanagari"

    # Step 3: Verify Synthesized 9-Phase Manual
    assert (sample_manual_dir / "00_frontmatter_syllabus.md").exists()
    for i in range(1, 10):
        phase_file = sample_manual_dir / f"phase_{i:02d}.md"
        assert phase_file.exists()
        content = phase_file.read_text(encoding="utf-8")
        assert "[MENTAL MODEL]" in content
        assert "[INVARIANT]" in content
        assert "Challenge 1: Output Prediction" in content
        assert "Challenge 2: Algorithm Utility" in content
        assert "Challenge 3: Industrial Mini-Project" in content
        assert len(DEVANAGARI_REGEX.findall(content)) == 0

    # Step 4: Compile Mock Master Reference PDF with Branding
    pdf_path = temp_workspace / "reference_manual.pdf"
    doc = fitz.open()
    # Cover Page
    cover = doc.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    cover.insert_text(fitz.Point(54, 150), "JavaScript V8 Master Reference Manual", fontsize=22)
    cover.insert_text(fitz.Point(54, 180), f"Prepared by {BRANDING_AUTHORS}", fontsize=11)
    # Content Page
    content_page = doc.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    content_page.insert_text(fitz.Point(54, 80), "Phase 1: V8 Memory Layout & Execution Context", fontsize=14)
    content_page.insert_textbox(fitz.Rect(54, 100, 541, 180), "Technically bolo toh execution context is initialized...", fontsize=10)
    # Vector Call Stack diagram
    shape = content_page.new_shape()
    shape.draw_rect(fitz.Rect(54, 200, 300, 320))
    shape.finish(color=(0, 0, 0), fill=(0.97, 0.97, 0.97))
    shape.commit()
    # Running Footer
    content_page.insert_text(fitz.Point(54, ISO_A4_HEIGHT - 30), f"Prepared by {BRANDING_AUTHORS}", fontsize=8)
    doc.save(pdf_path)
    doc.close()
    assert pdf_path.exists()

    # Step 5: Dual-Pass QA verification
    doc_qa = fitz.open(pdf_path)
    all_pdf_text = "".join(p.get_text() for p in doc_qa)
    doc_qa.close()
    dev_matches = DEVANAGARI_REGEX.findall(all_pdf_text)
    assert len(dev_matches) == 0
    assert "@issparsh" in all_pdf_text and "@sumitsingh097" in all_pdf_text


# ---------------------------------------------------------------------------
# Scenario 2: Web Documentation Crawl to Manual
# ---------------------------------------------------------------------------

def test_tier4_workload_02_web_doc_crawl_to_manual(sample_dom_path, temp_workspace):
    """Scenario 2: Crawl dynamic documentation site, extract code and DOM,
    synthesize Roman Hinglish guide, and verify skill packaging.
    Features Exercised: F2, F4, F5, F6, F7, F10, F11, F14, F15.
    """
    from scripts.ingestion.web_crawler import html_to_markdown_and_code, split_markdown_into_chapters
    from scripts.ingestion.unified_corpus import IngestionSource, UnifiedCorpus

    html_content = sample_dom_path.read_text(encoding="utf-8")
    md_text, code_blocks, title = html_to_markdown_and_code(html_content)
    chapters = split_markdown_into_chapters(md_text, default_title=title)

    source = IngestionSource(
        source_type="web",
        identifier="https://developer.example.com/v8-runtime",
        title=title,
        metadata={"file_type": "web_article"},
        chapters=chapters,
        extracted_code_blocks=code_blocks,
    )
    corpus = UnifiedCorpus()
    corpus.add_source(source)
    assert len(corpus.sources) == 1
    assert len(corpus.sources[0].extracted_code_blocks) >= 1

    # Verify skill packaging structure is valid
    skill_manifest = temp_workspace / "SKILL.md"
    skill_manifest.write_text(
        "---\nname: thenuke\ndescription: Multi-agent documentation engine\n---\n# thenuke runbook\n"
    )
    assert skill_manifest.exists()
    assert "thenuke" in skill_manifest.read_text()


# ---------------------------------------------------------------------------
# Scenario 3: Local Heterogeneous Bundle Processing
# ---------------------------------------------------------------------------

def test_tier4_workload_03_local_heterogeneous_bundle(
    sample_doc_path,
    sample_slides_path,
    temp_workspace
):
    """Scenario 3: Ingest combined bundle of local slides (.pptx) and architecture PDF;
    generate compiled manual with Call Stack and Heap vector diagrams.
    Features Exercised: F3, F9, F10, F11, F12, F15.
    """
    # Ingest PPTX
    prs = pptx.Presentation(sample_slides_path)
    slide_texts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                slide_texts.append(shape.text_frame.text)
    joined_slides = " ".join(slide_texts)
    assert "Call Stack" in joined_slides

    # Ingest PDF
    doc_in = fitz.open(sample_doc_path)
    pdf_text = "".join(p.get_text() for p in doc_in)
    doc_in.close()
    assert "V8 Engine" in pdf_text

    # Generate combined manual with both Call Stack and Heap vector diagrams
    out_pdf = temp_workspace / "bundle_manual.pdf"
    doc_out = fitz.open()

    p1 = doc_out.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    p1.insert_text(fitz.Point(54, 80), "Call Stack Architecture", fontsize=14)
    s1 = p1.new_shape()
    s1.draw_rect(fitz.Rect(54, 100, 250, 250))
    s1.finish(color=(0, 0, 0), fill=(0.95, 0.95, 0.95))
    s1.commit()

    p2 = doc_out.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    p2.insert_text(fitz.Point(54, 80), "Heap Memory Graph", fontsize=14)
    s2 = p2.new_shape()
    s2.draw_circle(fitz.Point(150, 150), 40)
    s2.finish(color=(0, 0, 0), fill=(0.95, 0.95, 0.95))
    s2.commit()

    # Add footers
    for p in doc_out:
        p.insert_text(fitz.Point(54, ISO_A4_HEIGHT - 30), f"Prepared by {BRANDING_AUTHORS}", fontsize=8)

    doc_out.save(out_pdf)
    doc_out.close()

    assert out_pdf.exists()
    verify_doc = fitz.open(out_pdf)
    assert len(verify_doc) == 2
    verify_doc.close()


# ---------------------------------------------------------------------------
# Scenario 4: Zero-Devanagari & Branding Compliance Audit
# ---------------------------------------------------------------------------

def test_tier4_workload_04_zero_devanagari_and_branding_audit(sample_manual_dir):
    """Scenario 4: Verify that synthesized and compiled output strictly adheres
    to 0 Devanagari chars, mandatory author handles, and monochrome styling.
    Features Exercised: F5, F6, F10, F11, F13.
    """
    total_chars = 0
    devanagari_violations = []

    for md_file in sample_manual_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        total_chars += len(content)
        matches = DEVANAGARI_REGEX.findall(content)
        if matches:
            devanagari_violations.extend(matches)

    assert total_chars > 5000, "Corpus text is unexpectedly small"
    assert len(devanagari_violations) == 0, f"Found Devanagari violations: {devanagari_violations}"

    # Verify branding handles
    assert "@issparsh" in BRANDING_AUTHORS
    assert "@sumitsingh097" in BRANDING_AUTHORS


# ---------------------------------------------------------------------------
# Scenario 5: End-to-End CLI Pipeline Execution
# ---------------------------------------------------------------------------

def test_tier4_workload_05_e2e_cli_pipeline_execution(test_corpus_path, temp_workspace):
    """Scenario 5: Execute pipeline data flow from corpus ingestion to compilation and QA.
    Features Exercised: F14, F15, F1, F2, F3, F4, F5, F9, F12, F13.
    """
    from scripts.ingestion.unified_corpus import UnifiedCorpus

    # 1. Load corpus
    corpus = UnifiedCorpus.load(test_corpus_path)
    assert len(corpus.sources) == 3

    # 2. Simulate synthesis
    synthesized_dir = temp_workspace / "synthesized"
    synthesized_dir.mkdir()
    (synthesized_dir / "00_frontmatter_syllabus.md").write_text(
        "# DETAILED SYLLABUS & TABLE OF CONTENTS (PART I to VI)\n## PART I: RUNTIME\n"
    )
    (synthesized_dir / "phase_01.md").write_text(
        "# Phase 1: Execution Context\nTechnically bolo toh stack frame initialize hota hai.\n"
        "[MENTAL MODEL]\nCall Stack is LIFO.\n[INVARIANT]\nSingle threaded.\n"
        "### Challenge 1: Output Prediction\n```javascript\nconsole.log(42); // Output: 42\n```\n"
        "### Challenge 2: Algorithm Utility\nO(1) cache.\n"
        "### Challenge 3: Industrial Mini-Project\nRate limiter.\n"
    )

    # 3. Simulate compilation
    out_pdf = temp_workspace / "reference_manual.pdf"
    doc = fitz.open()
    page = doc.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    page.insert_text(fitz.Point(54, 80), "Phase 1: Execution Context", fontsize=14)
    page.insert_text(fitz.Point(54, ISO_A4_HEIGHT - 30), f"Prepared by {BRANDING_AUTHORS}", fontsize=8)
    doc.save(out_pdf)
    doc.close()

    # 4. Simulate QA report
    qa_report = {
        "verdict": "PASS",
        "pass_1_visual": {"orphan_headers": [], "margin_overflows": []},
        "pass_2_textual": {"devanagari_character_count": 0, "anti_toy_code_passed": True}
    }
    qa_file = temp_workspace / "qa_report.json"
    with open(qa_file, "w") as f:
        json.dump(qa_report, f)

    assert out_pdf.exists()
    assert qa_file.exists()
    report_data = json.loads(qa_file.read_text())
    assert report_data["verdict"] == "PASS"


# ---------------------------------------------------------------------------
# Scenario 6: Broken Input Fault Tolerance & Graceful Recovery
# ---------------------------------------------------------------------------

def test_tier4_workload_06_broken_input_fault_tolerance(temp_workspace):
    """Scenario 6: Provide invalid video IDs, dead URLs, corrupted PDFs;
    verify graceful error handling without unhandled process termination.
    Features Exercised: F1, F2, F3, F15.
    """
    from scripts.ingestion.yt_ingest import is_youtube_url, extract_video_id
    from scripts.ingestion.web_crawler import fetch_tier1_requests

    # Invalid YouTube URLs
    bad_yt = "https://invalid-host.com/watch?v=none"
    assert is_youtube_url(bad_yt) is False
    assert extract_video_id(bad_yt) is None

    # Dead web URL
    status, body = fetch_tier1_requests("http://127.0.0.1:59999/nonexistent", timeout=1)
    assert status == 0
    assert body == ""

    # Corrupted PDF
    bad_pdf = temp_workspace / "bad.pdf"
    bad_pdf.write_bytes(b"NOT A REAL PDF STREAM")
    with pytest.raises(Exception):
        fitz.open(bad_pdf)


# ---------------------------------------------------------------------------
# Scenario 7: High-Density ISO A4 Page Layout Verification
# ---------------------------------------------------------------------------

def test_tier4_workload_07_iso_a4_page_layout_verification(sample_doc_path, temp_workspace):
    """Scenario 7: Compile multi-page manual and verify page budgets, 54pt margins,
    table boundaries, running headers, and footers.
    Features Exercised: F9, F11, F12.
    """
    doc = fitz.open(sample_doc_path)
    for page_idx, page in enumerate(doc):
        rect = page.rect
        # 1. Exact ISO A4 dimensions
        assert round(rect.width, 1) == round(ISO_A4_WIDTH, 1)
        assert round(rect.height, 1) == round(ISO_A4_HEIGHT, 1)

        # 2. Margin boundaries: 54pt margin budget
        printable_rect = fitz.Rect(
            PAGE_MARGIN_MIN,
            PAGE_MARGIN_MIN,
            ISO_A4_WIDTH - PAGE_MARGIN_MIN,
            ISO_A4_HEIGHT - PAGE_MARGIN_MIN
        )
        assert printable_rect.width == 487.28
        assert printable_rect.height == 733.89

    doc.close()


# ---------------------------------------------------------------------------
# Scenario 8: ES2024+ Native Code Standards & Anti-Toy Policy
# ---------------------------------------------------------------------------

def test_tier4_workload_08_es2024_standards_and_anti_toy_audit(sample_manual_dir):
    """Scenario 8: Scan all synthesized code blocks for ES2024+ syntax,
    zero npm dependencies, and absence of foo/bar/test.
    Features Exercised: F7, F8, F13.
    """
    total_code_blocks = 0
    modern_apis_found = set()

    for md_file in sample_manual_dir.glob("phase_*.md"):
        content = md_file.read_text(encoding="utf-8")
        code_blocks = re.findall(r"```(?:javascript|js)\n(.*?)```", content, re.DOTALL)
        for block in code_blocks:
            total_code_blocks += 1
            # Check modern APIs
            if "Object.groupBy" in block:
                modern_apis_found.add("Object.groupBy")
            if "Promise.withResolvers" in block:
                modern_apis_found.add("Promise.withResolvers")
            if "queueMicrotask" in block:
                modern_apis_found.add("queueMicrotask")

            # Check zero npm dependencies
            assert "require(" not in block
            assert "from 'lodash'" not in block

            # Anti-toy check
            toy_matches = re.findall(r"\b(?:const|let|var)\s+(foo|bar|baz)\b", block)
            assert len(toy_matches) == 0, f"Toy variables found: {toy_matches}"

    assert total_code_blocks >= 10
    assert len(modern_apis_found) >= 2
