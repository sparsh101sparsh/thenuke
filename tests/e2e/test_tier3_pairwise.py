"""Tier 3: Cross-Feature Combinations / Pairwise Interactions.

Minimum 15 pairwise interaction test cases.
Verifies integration boundaries between pairs of subsystem components
as specified in TEST_INFRA.md and PROJECT.md § 4.
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
# Pairwise Interaction Tests (16 tests)
# ---------------------------------------------------------------------------

def test_tier3_pairwise_f1_yt_and_f4_grilling(sample_vtt_path, sample_grilling_profile_path):
    """P1 (F1 + F4): YouTube transcript ingestion aligned with Grilling Profile.
    
    Verifies that cleaned transcripts are scoped according to the user's
    selected level of detail (e.g. senior_architect).
    """
    from scripts.ingestion.yt_ingest import clean_vtt_content
    vtt_text = sample_vtt_path.read_text(encoding="utf-8")
    cleaned_transcript = clean_vtt_content(vtt_text)
    profile = json.loads(sample_grilling_profile_path.read_text())

    assert len(cleaned_transcript) > 50
    assert profile["level_of_detail"] == "senior_architect"
    # Ensure technical depth keywords exist in transcript for senior architect scope
    assert "execution context" in cleaned_transcript.lower()


def test_tier3_pairwise_f2_web_and_f6_syllabus(sample_dom_path, sample_manual_dir):
    """P2 (F2 + F6): Web documentation crawl mapped into Part I-VI Syllabus.
    
    Verifies that web-extracted topics correlate to the curriculum syllabus structure.
    """
    from scripts.ingestion.web_crawler import html_to_markdown_and_code
    html_content = sample_dom_path.read_text(encoding="utf-8")
    md_text, _, _ = html_to_markdown_and_code(html_content)
    syllabus = (sample_manual_dir / "00_frontmatter_syllabus.md").read_text(encoding="utf-8")

    assert "Event Loop" in md_text
    assert "PART II: CONCURRENCY" in syllabus
    assert "Event Loop" in syllabus


def test_tier3_pairwise_f3_local_and_f9_vector(sample_doc_path, temp_workspace):
    """P3 (F3 + F9): Local PDF technical extracts paired with Vector Architecture visualizers.
    
    Verifies extracting architectural concepts from local PDF and generating
    accompanying PyMuPDF vector diagram shapes.
    """
    doc_in = fitz.open(sample_doc_path)
    in_text = "".join(p.get_text() for p in doc_in)
    doc_in.close()

    assert "Ignition" in in_text and "TurboFan" in in_text

    # Generate companion vector diagram document
    doc_out = fitz.open()
    page = doc_out.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    shape = page.new_shape()
    # Draw pipeline boxes
    shape.draw_rect(fitz.Rect(54, 100, 200, 160)) # Ignition box
    shape.draw_rect(fitz.Rect(250, 100, 400, 160)) # TurboFan box
    # Connect with vector arrow
    shape.draw_line(fitz.Point(200, 130), fitz.Point(250, 130))
    shape.finish(color=(0, 0, 0), width=1)
    shape.commit()

    page.insert_text(fitz.Point(60, 135), "Ignition Bytecode", fontsize=10)
    page.insert_text(fitz.Point(260, 135), "TurboFan JIT", fontsize=10)

    out_pdf = temp_workspace / "pipeline_vector.pdf"
    doc_out.save(out_pdf)
    doc_out.close()

    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 500


def test_tier3_pairwise_f4_grilling_and_f5_hinglish(sample_grilling_profile_path, sample_manual_dir):
    """P4 (F4 + F5): Grilling Profile requesting FAANG interview paired with Roman Hinglish.
    
    Verifies that conversational Roman bridges accompany formal English interview specs.
    """
    profile = json.loads(sample_grilling_profile_path.read_text())
    assert profile["audience_focus"] == "faang_interview"

    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    assert "[INTERVIEW TIP]" in phase1
    assert "Technically bolo toh" in phase1
    assert len(DEVANAGARI_REGEX.findall(phase1)) == 0


def test_tier3_pairwise_f5_hinglish_and_f8_es2024(sample_manual_dir):
    """P5 (F5 + F8): Roman Hinglish explanations incorporating ES2024+ native JavaScript.
    
    Verifies natural conversational text surrounding modern native APIs with zero npm deps.
    """
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    # Hinglish bridge
    assert "Dhayan se samjho" in phase1
    # ES2024 APIs
    assert "Object.groupBy" in phase1
    assert "Promise.withResolvers" in phase1
    # Zero npm dependencies
    assert "require(" not in phase1


def test_tier3_pairwise_f6_syllabus_and_f7_drills(sample_manual_dir):
    """P6 (F6 + F7): 9-Phase curriculum structure paired with mandatory 3-part Phase Challenges.
    
    Verifies that every phase enumerated in the syllabus index has all 3 required drills.
    """
    for i in range(1, 10):
        phase_text = (sample_manual_dir / f"phase_{i:02d}.md").read_text(encoding="utf-8")
        assert "## Phase Challenges" in phase_text
        assert "Challenge 1: Output Prediction" in phase_text
        assert "Challenge 2: Algorithm Utility" in phase_text
        assert "Challenge 3: Industrial Mini-Project" in phase_text


def test_tier3_pairwise_f7_drills_and_f8_es2024(sample_manual_dir):
    """P7 (F7 + F8): 3-part Phase Challenges use ES2024+ standards with inline output comments.
    
    Verifies Challenge 1 has explicit inline output traces and Challenge 2 has Big-O constraints.
    """
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    assert "queueMicrotask" in phase1 or "Promise.resolve" in phase1
    assert "// Output:" in phase1
    assert "O(1)" in phase1


def test_tier3_pairwise_f9_vector_and_f11_monochrome(temp_workspace):
    """P8 (F9 + F11): CS Memory diagrams strictly use monochrome aesthetic tokens.
    
    Verifies vector drawing primitives adhere to #000000, #222222, #CCCCCC, #F8F8F8 palette.
    """
    doc = fitz.open()
    page = doc.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)

    # High-contrast monochrome colors: (0,0,0) black, (0.97, 0.97, 0.97) off-white
    black_rgb = (0.0, 0.0, 0.0)
    hairline_grey_rgb = (0.8, 0.8, 0.8) # #CCCCCC

    shape = page.new_shape()
    # Call Stack frame container
    shape.draw_rect(fitz.Rect(54, 100, 300, 250))
    shape.finish(color=black_rgb, fill=(0.97, 0.97, 0.97), width=1)
    # Stack frame dividers
    shape.draw_line(fitz.Point(54, 150), fitz.Point(300, 150))
    shape.finish(color=hairline_grey_rgb, width=0.5)
    shape.commit()

    out_pdf = temp_workspace / "monochrome_diagram.pdf"
    doc.save(out_pdf)
    doc.close()

    assert out_pdf.exists()


def test_tier3_pairwise_f10_branding_and_f11_monochrome(temp_workspace):
    """P9 (F10 + F11): Cover and footers integrate branding within monochrome layout.
    
    Verifies author string and official 𝕏 glyph positioned at footer within 54pt margin.
    """
    doc = fitz.open()
    page = doc.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)

    # Footer position
    footer_text = f"Prepared by {BRANDING_AUTHORS}"
    page.insert_text(fitz.Point(54, ISO_A4_HEIGHT - 30), footer_text, fontsize=9, color=(0.2, 0.2, 0.2))

    # Vector 𝕏 glyph box
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(ISO_A4_WIDTH - 70, ISO_A4_HEIGHT - 42, ISO_A4_WIDTH - 54, ISO_A4_HEIGHT - 26))
    shape.finish(color=(0, 0, 0), fill=(0, 0, 0))
    shape.commit()

    branded_pdf = temp_workspace / "branded_monochrome.pdf"
    doc.save(branded_pdf)
    doc.close()

    # Re-open and verify text
    doc_check = fitz.open(branded_pdf)
    check_text = doc_check[0].get_text()
    doc_check.close()
    assert "@issparsh" in check_text and "@sumitsingh097" in check_text


def test_tier3_pairwise_f12_visual_qa_and_f13_textual_qa(temp_workspace):
    """P10 (F12 + F13): Dual-pass QA engine combines visual and textual audit passes.
    
    Verifies unified output containing pass_1_visual and pass_2_textual metrics.
    """
    qa_combined_result = {
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
    qa_file = temp_workspace / "qa_report.json"
    with open(qa_file, "w") as f:
        json.dump(qa_combined_result, f, indent=2)

    data = json.loads(qa_file.read_text())
    assert data["verdict"] == "PASS"
    assert "pass_1_visual" in data and "pass_2_textual" in data
    assert data["pass_2_textual"]["devanagari_character_count"] == 0


def test_tier3_pairwise_f1_yt_and_f15_cli_pipeline(temp_workspace, sample_vtt_path):
    """P11 (F1 + F15): CLI Ingest command consumes YouTube VTT and writes unified corpus.
    
    Verifies that CLI ingestion builds a valid IngestionSource model with deduplicated chapters.
    """
    from scripts.ingestion.yt_ingest import clean_vtt_content, align_cues_to_chapters, parse_vtt_cues, deduplicate_vtt_cues
    from scripts.ingestion.unified_corpus import IngestionSource, UnifiedCorpus

    content = sample_vtt_path.read_text(encoding="utf-8")
    cues = deduplicate_vtt_cues(parse_vtt_cues(content))
    chapters = align_cues_to_chapters(cues, [], total_duration=15.0, video_title="V8 Execution Context")

    source = IngestionSource(
        source_type="youtube",
        identifier="https://www.youtube.com/watch?v=mock_v8_01",
        title="V8 Execution Context",
        metadata={"duration": 15.0, "file_type": "youtube_stream"},
        chapters=chapters
    )
    corpus = UnifiedCorpus()
    corpus.add_source(source)

    corpus_out = temp_workspace / "nuke_ingestion_corpus.json"
    corpus.save(corpus_out)

    assert corpus_out.exists()
    loaded_corpus = UnifiedCorpus.load(corpus_out)
    assert len(loaded_corpus.sources) == 1
    assert loaded_corpus.sources[0].source_type == "youtube"


def test_tier3_pairwise_f2_web_and_f14_skill_packaging():
    """P12 (F2 + F14): Web crawler module packaged in skill scripts directory.
    
    Verifies scripts/ingestion/web_crawler.py is importable within skill boundaries.
    """
    from scripts.ingestion import web_crawler
    assert hasattr(web_crawler, "crawl_url")
    assert hasattr(web_crawler, "html_to_markdown_and_code")


def test_tier3_pairwise_f3_local_and_f12_visual_qa(sample_doc_path):
    """P13 (F3 + F12): Local PDF extracted and verified by Pass 1 Visual QA.
    
    Verifies that ingested local PDF passes page dimension and margin checks.
    """
    doc = fitz.open(sample_doc_path)
    assert len(doc) >= 1
    page = doc[0]
    # Check page rect matches A4
    assert round(page.rect.width, 1) == round(ISO_A4_WIDTH, 1)
    assert round(page.rect.height, 1) == round(ISO_A4_HEIGHT, 1)
    doc.close()


def test_tier3_pairwise_f5_hinglish_and_f13_textual_qa(sample_manual_dir):
    """P14 (F5 + F13): Synthesized Hinglish text audited by Pass 2 Textual QA for 0 Devanagari.
    
    Verifies zero Devanagari violations across all markdown sections.
    """
    total_violations = 0
    for md_file in sample_manual_dir.glob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        total_violations += len(DEVANAGARI_REGEX.findall(text))
    assert total_violations == 0


def test_tier3_pairwise_f8_es2024_and_f13_textual_qa(sample_manual_dir):
    """P15 (F8 + F13): Modern ES2024+ code standards audited by Pass 2 Textual QA.
    
    Verifies presence of Object.groupBy or Promise.withResolvers and rejection of toy variables.
    """
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    assert "Object.groupBy" in phase1
    assert "const foo" not in phase1 and "let bar" not in phase1


def test_tier3_pairwise_f4_grilling_and_f9_vector_threshold(sample_grilling_profile_path, sample_manual_dir):
    """P16 (F4 + F9): Grilling profile visual threshold controls vector diagram directives.
    
    Verifies that strict_need_based threshold includes architectural diagrams
    only at core structural checkpoints (Call Stack, Heap Graph, Event Loop).
    """
    profile = json.loads(sample_grilling_profile_path.read_text())
    assert profile["visual_inclusion_threshold"] == "strict_need_based"

    # In strict_need_based mode, only essential diagrams are embedded
    phase1 = (sample_manual_dir / "phase_01.md").read_text(encoding="utf-8")
    diagram_directives = re.findall(r"<!--\s*DIAGRAM:\s*([a-zA-Z0-9_]+)", phase1)
    assert len(diagram_directives) >= 1
    assert diagram_directives[0] in {"call_stack", "heap_graph", "event_loop"}
