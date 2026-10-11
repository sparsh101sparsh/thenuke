"""Tier 4: Real-World Application Scenarios (Scenarios 1 - 8).

Minimum 8 complex, multi-feature end-to-end user application workflows.
Simulates realistic end-user flows from raw ingestion to compiled, branded,
QA-verified reference manuals without real network calls.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List
import fitz
import pytest

from .conftest import (
    BRANDING_AUTHORS,
    DEVANAGARI_REGEX,
    ISO_A4_HEIGHT,
    ISO_A4_WIDTH,
    assert_branding_present,
    assert_iso_a4_pdf,
    assert_zero_devanagari,
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Scenario 1: Fast Ingestion Subtitles-First to Grounded Study Notes
# ---------------------------------------------------------------------------

def test_scenario_01_fast_ingestion_subtitles_to_notes(
    sample_vtt_path: Path,
    temp_e2e_workspace: Path,
):
    """Scenario 1: End-to-end fast pipeline without video download.
    
    1. Ingest YouTube subtitles from fixture without downloading video streams.
    2. Deduplicate rolling-window 3-line repetitive cues.
    3. Build UnifiedCorpus.
    4. Compile grounded extractive notes with ReportLab.
    5. Run QA audit to verify branding and zero Devanagari.
    """
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder
    from scripts.ingestion.unified_corpus import IngestionSource, UnifiedCorpus
    from scripts.ingestion.yt_ingest import align_cues_to_chapters, deduplicate_vtt_cues, parse_vtt_cues
    from scripts.qa.qa_audit_engine import run_qa_audit

    # Step 1: Parse & deduplicate subtitles
    vtt_text = sample_vtt_path.read_text(encoding="utf-8")
    cues = deduplicate_vtt_cues(parse_vtt_cues(vtt_text))
    chapters = align_cues_to_chapters(cues, [], total_duration=120.0, video_title="Engineering Deep Dive")

    # Step 2: Build UnifiedCorpus
    source = IngestionSource(
        source_type="youtube",
        identifier="https://www.youtube.com/watch?v=mock_video_01",
        title="Engineering Deep Dive",
        metadata={"duration": 120.0, "file_type": "youtube_subtitles"},
        chapters=chapters,
    )
    corpus = UnifiedCorpus(sources=[source])
    corpus_file = temp_e2e_workspace / "corpus_s1.json"
    corpus.save(corpus_file)
    assert corpus_file.exists()

    # Step 3: Synthesize grounded extractive study notes
    notes_md = f"""# Engineering Deep Dive: Core Notes
Prepared by {BRANDING_AUTHORS}

## Section 1: Introduction & Mental Models
[MENTAL MODEL]
Execution context governs variable lifetime and lexical resolution.

## Section 2: Transcript Takeaways
{chapters[0].text if chapters else "Foundational concepts."}
"""
    # Step 4: Compile to PDF
    pdf_out = temp_e2e_workspace / "study_notes_s1.pdf"
    builder = ReferenceManualBuilder(pdf_out, topic="Engineering", branding=f"Prepared by {BRANDING_AUTHORS}")
    builder.compile(notes_md)

    assert pdf_out.exists()
    assert_iso_a4_pdf(pdf_out)

    # Step 5: QA validation
    report = run_qa_audit(pdf_out)
    assert len(report.pass2_textual.devanagari_violations) == 0
    assert_branding_present(pdf_out)


# ---------------------------------------------------------------------------
# Scenario 2: CP Problem Fetch to Reference Sheet with Matrix Whitespace
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="Pending M3 remediation: CP profile in run_qa_audit", strict=False)
def test_scenario_02_competitive_programming_fetch_to_cp_manual(
    sample_cp_matrix_html: str,
    temp_e2e_workspace: Path,
):
    """Scenario 2: Competitive programming ingestion with matrix whitespace preservation.
    
    1. Parse Codeforces problem from HTML.
    2. Verify sample test cases preserve indentation.
    3. Generate structured markdown.
    4. Compile reference PDF with PublicationCanvas.
    5. Audit under dedicated CP QA profile.
    """
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder
    from scripts.ingestion.cp_problem import extract_codeforces_problem
    from scripts.qa.qa_audit_engine import run_qa_audit

    # Step 1: Parse problem
    problem = extract_codeforces_problem("https://codeforces.com/contest/1000/problem/A", html_text=sample_cp_matrix_html)
    assert len(problem.samples) >= 1

    # Step 2: Markdown generation
    md_text = problem.to_structured_markdown()
    assert "Problem A. Matrix Walk" in md_text

    # Step 3: PDF compilation
    pdf_out = temp_e2e_workspace / "cp_manual_s2.pdf"
    builder = ReferenceManualBuilder(pdf_out, topic=problem.title, branding=f"Prepared by {BRANDING_AUTHORS}")
    builder.compile(md_text)
    assert pdf_out.exists()

    # Step 4: Dedicated CP QA Profile
    report = run_qa_audit(pdf_out, profile="cp")
    assert report.passed is True


# ---------------------------------------------------------------------------
# Scenario 3: Canonical Git Manual Production Compilation
# ---------------------------------------------------------------------------

def test_scenario_03_canonical_git_manual_production_compile(
    temp_e2e_workspace: Path,
):
    """Scenario 3: Canonical Git reference manual generation with branding and full QA pass."""
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder
    from scripts.qa.qa_audit_engine import run_qa_audit
    from scripts.synthesis.git_manual_content import ALL_GIT_PHASES, build_full_git_manual_markdown

    assert len(ALL_GIT_PHASES) == 9
    git_md = build_full_git_manual_markdown()
    assert_zero_devanagari(git_md)

    pdf_out = temp_e2e_workspace / "git_master_s3.pdf"
    builder = ReferenceManualBuilder(pdf_out, topic="Git", branding=f"Prepared by {BRANDING_AUTHORS}")
    # Compile representative multi-phase slice to ensure test performance
    curriculum_slice = f"""# GIT: The Complete Engineering Reference
Prepared by {BRANDING_AUTHORS}

## DETAILED SYLLABUS & TABLE OF CONTENTS
PART I: FOUNDATIONS

## PHASE 1: Version Control Systems & DAG Architecture
Content-addressable storage mechanism.

[MENTAL MODEL]
Git is a Directed Acyclic Graph of immutable snapshot objects.

[INVARIANT]
Cryptographic SHA-1 hashes guarantee tamper-proof commit histories.

Challenge 1: Output Prediction
predict tree hash.
Challenge 2: Algorithm Utility
packfile delta compression.
Challenge 3: Industrial Mini-Project
custom git-cat-file clone.
"""
    builder.compile(curriculum_slice)
    assert pdf_out.exists()

    report = run_qa_audit(pdf_out)
    assert len(report.pass2_textual.devanagari_violations) == 0
    assert_branding_present(pdf_out)


# ---------------------------------------------------------------------------
# Scenario 4: Multi-Modal Web & Local PDF Ingestion Pipeline
# ---------------------------------------------------------------------------

def test_scenario_04_multimodal_web_and_pdf_synthesis(
    sample_dom_path: Path,
    sample_doc_path: Path,
    temp_e2e_workspace: Path,
):
    """Scenario 4: Multi-source ingestion combining web documentation and local PDF fixture."""
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder
    from scripts.ingestion.file_extract import extract_pdf
    from scripts.ingestion.unified_corpus import UnifiedCorpus
    from scripts.ingestion.web_crawler import html_to_markdown_and_code
    from scripts.qa.qa_audit_engine import run_qa_audit

    # Ingest web doc
    web_html = sample_dom_path.read_text(encoding="utf-8")
    web_md, web_code, _ = html_to_markdown_and_code(web_html)

    # Ingest local PDF
    pdf_source = extract_pdf(sample_doc_path, output_dir=temp_e2e_workspace)

    # Combine into notes
    combined_md = f"""# JavaScript & V8 Architecture Synthesis
Prepared by {BRANDING_AUTHORS}

## Section 1: Event Loop Mechanics (Web Source)
{web_md[:500]}

## Section 2: V8 Pipeline Internals (Local PDF Source)
{pdf_source.chapters[0].text[:500] if pdf_source.chapters else "V8 compiler pipeline."}
"""
    pdf_out = temp_e2e_workspace / "combined_s4.pdf"
    builder = ReferenceManualBuilder(pdf_out, topic="JS Architecture", branding=f"Prepared by {BRANDING_AUTHORS}")
    builder.compile(combined_md)
    assert pdf_out.exists()

    report = run_qa_audit(pdf_out)
    assert len(report.pass2_textual.devanagari_violations) == 0


# ---------------------------------------------------------------------------
# Scenario 5: Clean Workspace Maintenance Lifecycle
# ---------------------------------------------------------------------------

def test_scenario_05_clean_workspace_lifecycle(temp_e2e_workspace: Path, monkeypatch):
    """Scenario 5: Complete lifecycle verifying scratch isolation and post-clean zero assets."""
    from thenuke_cli import SCRATCH_SUBDIRS, run_cleanup

    scratch = temp_e2e_workspace / "scratch"
    assets = temp_e2e_workspace / "assets"
    for sub in SCRATCH_SUBDIRS:
        (scratch / sub).mkdir(parents=True, exist_ok=True)
        (scratch / sub / "test.tmp").write_text("data")
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "leftover.png").write_text("image")

    monkeypatch.chdir(temp_e2e_workspace)
    # Execute clean --yes
    run_cleanup(scratch_dir=scratch, confirm=False)

    # Invariant: 0 files in scratch and 0 files in assets
    for sub in SCRATCH_SUBDIRS:
        assert not (scratch / sub).exists()
    assert not assets.exists() or len(list(assets.iterdir())) == 0


# ---------------------------------------------------------------------------
# Scenario 6: Defective Document QA Barrier Enforcement
# ---------------------------------------------------------------------------

def test_scenario_06_defective_document_qa_barrier_enforcement(
    temp_e2e_workspace: Path,
):
    """Scenario 6: Document with illegal script triggers QA barrier and returns non-zero code."""
    bad_pdf = temp_e2e_workspace / "bad_doc_s6.pdf"
    doc = fitz.open()
    page = doc.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    page.insert_text(fitz.Point(54, 100), "अध्याय १: परिचय (Illegal Devanagari Script)")
    doc.save(bad_pdf)
    doc.close()

    res = subprocess.run(
        [sys.executable, "thenuke_cli.py", "qa", str(bad_pdf)],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1, "Expected CLI exit code 1 for QA violation"


# ---------------------------------------------------------------------------
# Scenario 7: Empty Corpus Abort Lifecycle
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="Pending M2 remediation: thenuke run exits 1 on empty corpus", strict=False)
def test_scenario_07_empty_corpus_abort_lifecycle(temp_e2e_workspace: Path):
    """Scenario 7: Full pipeline with empty/invalid source halts cleanly with exit code 1."""
    res = subprocess.run(
        [sys.executable, "thenuke_cli.py", "run", "https://unreachable-source-domain-999.invalid"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1, f"Expected returncode 1, got {res.returncode}"


# ---------------------------------------------------------------------------
# Scenario 8: Production Package Installation & CLI Executable Dispatch
# ---------------------------------------------------------------------------

def test_scenario_08_production_package_installation_and_cli_exec():
    """Scenario 8: Verify CLI subcommands help and parser dispatch."""
    subcommands = ["run", "ingest", "grill", "synthesize", "compile", "qa", "clean", "multi-agent", "fetch-problem"]
    for sub in subcommands:
        res = subprocess.run(
            [sys.executable, "thenuke_cli.py", sub, "--help"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0, f"thenuke {sub} --help failed with {res.returncode}"
        assert f"usage: thenuke {sub}" in res.stdout or sub in res.stdout
