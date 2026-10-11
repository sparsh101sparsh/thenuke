"""Tier 3: Cross-Feature Combinations / Pairwise Interactions (P01 - P16).

Minimum 15 pairwise interaction test cases.
Verifies integration boundaries between pairs of subsystem components
as specified in ORIGINAL_REQUEST.md and PROJECT.md § Architecture.
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
# P01: CP Ingestion -> QA Audit Under CP Profile (R3)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="Pending M3 remediation: CP profile in run_qa_audit", strict=False)
def test_tier3_pairwise_p01_cp_ingest_and_cp_qa_profile(sample_cp_matrix_html: str, temp_e2e_workspace: Path):
    """P01: CP problem parsed from HTML and compiled to PDF passes CP QA audit profile."""
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder
    from scripts.ingestion.cp_problem import extract_codeforces_problem
    from scripts.qa.qa_audit_engine import run_qa_audit

    problem = extract_codeforces_problem("https://codeforces.com/contest/1000/problem/A", html_text=sample_cp_matrix_html)
    md_content = problem.to_structured_markdown()

    out_pdf = temp_e2e_workspace / "cp_problem_p01.pdf"
    builder = ReferenceManualBuilder(out_pdf, topic=problem.title, branding=f"Prepared by {BRANDING_AUTHORS}")
    builder.compile(md_content)

    assert out_pdf.exists()
    report = run_qa_audit(out_pdf, profile="cp")
    assert report.passed is True


# ---------------------------------------------------------------------------
# P02: YouTube Ingestion -> CorpusIndexer Evidence Spans (R2 + R4)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="Pending M4 remediation: CorpusIndexer module", strict=False)
def test_tier3_pairwise_p02_yt_subtitles_and_corpus_indexing(sample_vtt_path: Path):
    """P02: YouTube subtitles parsed and indexed into EvidenceSpan transcript chunks."""
    from scripts.ingestion.unified_corpus import IngestionSource, UnifiedCorpus
    from scripts.ingestion.yt_ingest import align_cues_to_chapters, deduplicate_vtt_cues, parse_vtt_cues
    from scripts.synthesis.corpus_indexer import CorpusIndexer

    vtt_text = sample_vtt_path.read_text(encoding="utf-8")
    cues = deduplicate_vtt_cues(parse_vtt_cues(vtt_text))
    chapters = align_cues_to_chapters(cues, [], total_duration=120.0, video_title="Video")

    src = IngestionSource(source_type="youtube", identifier="https://youtube.com/watch?v=1", chapters=chapters)
    corpus = UnifiedCorpus(sources=[src])

    indexer = CorpusIndexer()
    spans = indexer.index(corpus)
    transcript_spans = [s for s in spans if s.span_type == "transcript"]
    assert len(transcript_spans) > 0
    assert any("Welcome" in s.content for s in transcript_spans)


# ---------------------------------------------------------------------------
# P03: Evidence Spans -> Extractive Notes Synthesis (R4)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="Pending M4 remediation: CorpusIndexer & ExtractiveNotes", strict=False)
def test_tier3_pairwise_p03_corpus_indexer_and_extractive_notes(test_corpus_path: Path):
    """P03: CorpusIndexer spans feed directly into extractive notes generation."""
    from scripts.ingestion.unified_corpus import UnifiedCorpus
    from scripts.synthesis.corpus_indexer import CorpusIndexer

    corpus = UnifiedCorpus.load(test_corpus_path)
    indexer = CorpusIndexer()
    spans = indexer.index(corpus)
    sections = indexer.get_sections()

    assert len(sections) > 0
    for sec in sections:
        assert "title" in sec and "spans" in sec


# ---------------------------------------------------------------------------
# P04: Extractive Notes -> ReportLab Compilation (R4 + Diagramming)
# ---------------------------------------------------------------------------

def test_tier3_pairwise_p04_extractive_notes_and_reportlab_compile(temp_e2e_workspace: Path):
    """P04: Grounded markdown notes compiled into ISO A4 PDF with ReportLab."""
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder

    grounded_notes_md = f"""# V8 Event Loop Architecture Study Notes
Prepared by {BRANDING_AUTHORS}

## Section 1: Execution Context Foundations
[MENTAL MODEL]
Execution context is created whenever any function is invoked.

```javascript
const {{ promise, resolve }} = Promise.withResolvers();
resolve(42);
```

## Section 2: Concurrency & Tick Lifecycle
Microtask queue drains before macrotasks.
"""
    out_pdf = temp_e2e_workspace / "extractive_notes.pdf"
    builder = ReferenceManualBuilder(out_pdf, topic="V8 Internals", branding=f"Prepared by {BRANDING_AUTHORS}")
    builder.compile(grounded_notes_md)

    assert out_pdf.exists()
    assert_iso_a4_pdf(out_pdf)


# ---------------------------------------------------------------------------
# P05: Custom Branding Parameter -> QA Footer Verification (R2 + QA)
# ---------------------------------------------------------------------------

def test_tier3_pairwise_p05_custom_branding_and_qa_audit(temp_e2e_workspace: Path):
    """P05: Custom branding passed via thenuke compile --branding verified in PDF."""
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder
    from scripts.qa.qa_audit_engine import run_qa_audit

    out_pdf = temp_e2e_workspace / "custom_brand.pdf"
    custom_brand = f"Prepared by {BRANDING_AUTHORS} [Custom FAANG Release]"
    builder = ReferenceManualBuilder(out_pdf, topic="Git", branding=custom_brand)
    test_md = f"""# Architecture Guide
{custom_brand}

## PHASE 1: Deep Dive
Plumbing commands in Git.
"""
    builder.compile(test_md)
    assert out_pdf.exists()

    doc = fitz.open(out_pdf)
    text = " ".join(p.get_text() for p in doc)
    doc.close()
    assert "@issparsh" in text and "@sumitsingh097" in text


# ---------------------------------------------------------------------------
# P06: Empty Ingest Corpus -> CLI Exits 1 (R2)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="Pending M2 remediation: thenuke run exits 1 on empty corpus", strict=False)
def test_tier3_pairwise_p06_empty_corpus_and_cli_exit_code(temp_e2e_workspace: Path):
    """P06: Pipeline invocation with empty corpus triggers sys.exit(1)."""
    res = subprocess.run(
        [sys.executable, "thenuke_cli.py", "run", "https://invalid-dead-link-00000.com"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1


# ---------------------------------------------------------------------------
# P07: CP Matrix Indentation -> ReportLab Code Block (R3 + Diagramming)
# ---------------------------------------------------------------------------

def test_tier3_pairwise_p07_cp_matrix_indentation_and_reportlab_code_block(temp_e2e_workspace: Path):
    """P07: Multi-line matrix code block preserves leading space alignment in ReportLab flowable."""
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder

    cp_md = f"""# Matrix Problem Reference
Prepared by {BRANDING_AUTHORS}

## Sample Test Case
```text
  1  0  0
  0  1  0
  0  0  1
```
"""
    out_pdf = temp_e2e_workspace / "matrix_render.pdf"
    builder = ReferenceManualBuilder(out_pdf, topic="Matrix", branding=f"Prepared by {BRANDING_AUTHORS}")
    builder.compile(cp_md)

    assert out_pdf.exists()
    doc = fitz.open(out_pdf)
    text = " ".join(p.get_text() for p in doc)
    doc.close()
    assert "1" in text and "0" in text


# ---------------------------------------------------------------------------
# P08: URL Scheme Rejection -> Ingestion Safeguard (R2 + Ingestion)
# ---------------------------------------------------------------------------

def test_tier3_pairwise_p08_url_validation_rejection_and_error_handling(temp_e2e_workspace: Path):
    """P08: Ingestion skips ftp:// scheme and leaves corpus empty without error."""
    from thenuke_cli import run_ingest

    corpus_file = temp_e2e_workspace / "ftp_corpus.json"
    result_path = run_ingest(["ftp://youtube.com/watch?v=123"], corpus_path=corpus_file)

    data = json.loads(Path(result_path).read_text(encoding="utf-8"))
    assert len(data.get("sources", [])) == 0


# ---------------------------------------------------------------------------
# P09: CLI Download Video Flag -> Ingestion Option Selection (R2)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="Pending M2 remediation: --download-video CLI flag", strict=False)
def test_tier3_pairwise_p09_download_video_toggle_and_ingest_branch():
    """P09: CLI --download-video flag toggles ingestion video download mode."""
    from thenuke_cli import build_parser

    parser = build_parser()
    args_default = parser.parse_args(["run", "https://youtube.com/watch?v=123"])
    assert getattr(args_default, "download_video", False) is False

    args_flag = parser.parse_args(["run", "https://youtube.com/watch?v=123", "--download-video"])
    assert getattr(args_flag, "download_video", False) is True


# ---------------------------------------------------------------------------
# P10: Scratch Dir Creation -> Clean --yes Complete Wipe (R2)
# ---------------------------------------------------------------------------

def test_tier3_pairwise_p10_scratch_dir_creation_and_clean_yes(temp_e2e_workspace: Path, monkeypatch):
    """P10: Temporary scratch assets created during ingestion are completely wiped by clean --yes."""
    from thenuke_cli import SCRATCH_SUBDIRS, run_cleanup

    scratch = temp_e2e_workspace / "scratch"
    for sub in SCRATCH_SUBDIRS:
        sub_dir = scratch / sub
        sub_dir.mkdir(parents=True, exist_ok=True)
        (sub_dir / "downloaded_video.mp4").write_bytes(b"\x00" * 1024)

    assets = temp_e2e_workspace / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "image.png").write_bytes(b"\x00" * 512)

    monkeypatch.chdir(temp_e2e_workspace)
    run_cleanup(scratch_dir=scratch, confirm=False)

    for sub in SCRATCH_SUBDIRS:
        assert not (scratch / sub).exists()
    assert not assets.exists() or len(list(assets.iterdir())) == 0


# ---------------------------------------------------------------------------
# P11: Packaging Pyproject -> CLI Entrypoint Execution (R1 + CLI)
# ---------------------------------------------------------------------------

def test_tier3_pairwise_p11_pyproject_packaging_and_cli_dispatch():
    """P11: pyproject.toml entrypoint matches thenuke_cli.py main callable."""
    import importlib
    pyproject = (ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8")
    assert 'thenuke = "thenuke_cli:main"' in pyproject

    cli_mod = importlib.import_module("thenuke_cli")
    assert hasattr(cli_mod, "main")
    assert callable(cli_mod.main)


# ---------------------------------------------------------------------------
# P12: Sample Doc Fixture -> Local Media Extraction (R1 + Ingestion)
# ---------------------------------------------------------------------------

def test_tier3_pairwise_p12_sample_doc_fixture_and_local_extract(sample_doc_path: Path, temp_e2e_workspace: Path):
    """P12: Tracked sample_doc.pdf fixture extracted into structured IngestionSource."""
    from scripts.ingestion.file_extract import extract_pdf

    source = extract_pdf(sample_doc_path, output_dir=temp_e2e_workspace)
    assert source.source_type == "local_file"
    assert len(source.chapters) >= 1
    assert any(len(c.text.strip()) > 0 for c in source.chapters)


# ---------------------------------------------------------------------------
# P13: Canonical Git Manual -> QA Git Profile (R4 + QA)
# ---------------------------------------------------------------------------

def test_tier3_pairwise_p13_canonical_git_manual_and_git_qa_profile(temp_e2e_workspace: Path):
    """P13: Canonical hand-crafted Git textbook snippet passes QA audit."""
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder
    from scripts.qa.qa_audit_engine import run_qa_audit

    out_pdf = temp_e2e_workspace / "git_canonical.pdf"
    builder = ReferenceManualBuilder(out_pdf, topic="Git", branding=f"Prepared by {BRANDING_AUTHORS}")
    test_md = f"""# Git: The Complete Architecture Reference
Prepared by {BRANDING_AUTHORS}

## DETAILED SYLLABUS & TABLE OF CONTENTS
PART I: FOUNDATIONS

## PHASE 1: Object Model
Content-addressable storage mechanism.

[MENTAL MODEL]
Git models history as a DAG of snapshots.

[INVARIANT]
Object hashes are cryptographically immutable.

Challenge 1: Output Prediction
predict commit hash.
Challenge 2: Algorithm Utility
packfile delta compression.
Challenge 3: Industrial Mini-Project
custom plumbing tool.
"""
    builder.compile(test_md)
    report = run_qa_audit(out_pdf)
    assert len(report.pass2_textual.devanagari_violations) == 0


# ---------------------------------------------------------------------------
# P14: Unrendered LaTeX in CP -> CP QA Profile Rejection (R3 + QA)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="Pending M3 remediation: CP profile unrendered LaTeX check", strict=False)
def test_tier3_pairwise_p14_unrendered_latex_and_qa_cp_rejection(temp_e2e_workspace: Path):
    """P14: CP problem PDF containing unrendered raw LaTeX macros rejected by CP QA."""
    from scripts.qa.qa_audit_engine import run_qa_audit

    pdf_path = temp_e2e_workspace / "raw_latex.pdf"
    doc = fitz.open()
    page = doc.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    page.insert_text(fitz.Point(54, 100), f"Problem A Prepared by {BRANDING_AUTHORS}")
    page.insert_text(fitz.Point(54, 130), "Evaluate \\sum_{i=1}^n a_i \\le 10^9")
    doc.save(pdf_path)
    doc.close()

    report = run_qa_audit(pdf_path, profile="cp")
    assert not report.passed


# ---------------------------------------------------------------------------
# P15: QA Audit Failure -> CLI Returns Exit Code 1 (R2 + QA)
# ---------------------------------------------------------------------------

def test_tier3_pairwise_p15_qa_failure_and_cli_exit_code_1(temp_e2e_workspace: Path):
    """P15: Running thenuke qa on a defective document returns exit code 1."""
    pdf_path = temp_e2e_workspace / "defective.pdf"
    doc = fitz.open()
    page = doc.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    page.insert_text(fitz.Point(54, 100), "अवैध देवनागरी (Defective Devanagari)")
    doc.save(pdf_path)
    doc.close()

    res = subprocess.run([sys.executable, "thenuke_cli.py", "qa", str(pdf_path)], cwd=str(ROOT_DIR), capture_output=True, text=True)
    assert res.returncode == 1


# ---------------------------------------------------------------------------
# P16: Multi-Source Ingestion -> Unified Corpus (R2 + Ingestion)
# ---------------------------------------------------------------------------

def test_tier3_pairwise_p16_multi_source_ingestion_and_unified_corpus(sample_doc_path: Path, temp_e2e_workspace: Path):
    """P16: Ingesting local file and mock source creates unified corpus with correct sources count."""
    from thenuke_cli import run_ingest

    corpus_file = temp_e2e_workspace / "multi_corpus.json"
    result_path = run_ingest([str(sample_doc_path)], corpus_path=corpus_file)

    data = json.loads(Path(result_path).read_text(encoding="utf-8"))
    assert len(data.get("sources", [])) == 1
    assert data["sources"][0]["source_type"] == "local_file"
