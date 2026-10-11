"""E2E Test Suite Fixtures and Configuration.

Provides self-contained fixtures, temporary isolated workspace isolation,
and sample payloads for the 4-tier E2E test suite.
"""

from __future__ import annotations

import os
import re
import json
import shutil
import tempfile
from pathlib import Path
from typing import Generator
import pytest
import fitz

# Core requirement invariants from ORIGINAL_REQUEST.md & PROJECT.md
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F\uA8E0-\uA8FF\u1CD0-\u1CFF]")
BRANDING_AUTHORS = "@issparsh @sumitsingh097"
ISO_A4_WIDTH = 595.28
ISO_A4_HEIGHT = 841.89
PAGE_MARGIN_MIN = 54.0

MONOCHROME_PALETTE = {
    "#000000", "#222222", "#444444", "#666666", "#777777",
    "#CCCCCC", "#EFEFEF", "#F1F5F9", "#F8F8F8", "#FFFFFF"
}


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Absolute path to the shared test fixtures directory."""
    path = Path(__file__).resolve().parent.parent / "fixtures"
    assert path.exists(), f"Fixtures directory missing: {path}"
    return path


@pytest.fixture(scope="session")
def sample_doc_path(fixtures_dir: Path) -> Path:
    """Path to tracked sample_doc.pdf fixture (ORIGINAL_REQUEST R1)."""
    pdf_path = fixtures_dir / "sample_doc.pdf"
    assert pdf_path.exists(), f"sample_doc.pdf fixture missing at {pdf_path}"
    return pdf_path


@pytest.fixture(scope="session")
def sample_vtt_path(fixtures_dir: Path) -> Path:
    """Path to sample WebVTT subtitle fixture."""
    return fixtures_dir / "sample_vtt.vtt"


@pytest.fixture(scope="session")
def sample_slides_path(fixtures_dir: Path) -> Path:
    """Path to sample PPTX presentation fixture."""
    return fixtures_dir / "sample_slides.pptx"


@pytest.fixture(scope="session")
def sample_dom_path(fixtures_dir: Path) -> Path:
    """Path to sample DOM HTML capture fixture."""
    return fixtures_dir / "sample_dom.html"


@pytest.fixture(scope="session")
def test_corpus_path(fixtures_dir: Path) -> Path:
    """Path to pre-built test corpus fixture."""
    return fixtures_dir / "test_corpus.json"


@pytest.fixture(scope="session")
def sample_manual_dir(fixtures_dir: Path) -> Path:
    """Path to sample synthesized manual directory."""
    return fixtures_dir / "sample_synthesized_manual"


@pytest.fixture
def temp_e2e_workspace() -> Generator[Path, None, None]:
    """Isolated temporary workspace for test side-effects."""
    tmp = Path(tempfile.mkdtemp(prefix="nuke_e2e_"))
    try:
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope="session")
def sample_cp_matrix_html() -> str:
    """Codeforces-like HTML problem with leading-space indented matrix sample test cases."""
    return """<!DOCTYPE html>
<html>
<head><title>Problem 1000A - Matrix Walk</title></head>
<body>
<div class="problem-statement">
  <div class="header">
    <div class="title">A. Matrix Walk</div>
    <div class="time-limit"><div class="property-title">time limit per test</div>1.0 s</div>
    <div class="memory-limit"><div class="property-title">memory limit per test</div>256 MB</div>
  </div>
  <div>
    <p>Given a $2 \\times 3$ grid of integers, find the maximum path sum.</p>
  </div>
  <div class="input-specification">
    <div class="section-title">Input</div>
    <p>The first line contains $n$ and $m$ ($1 \\le n, m \\le 100$).</p>
  </div>
  <div class="output-specification">
    <div class="section-title">Output</div>
    <p>Print the matrix values with exact spacing preserved.</p>
  </div>
  <div class="sample-tests">
    <div class="section-title">Examples</div>
    <div class="sample-test">
      <div class="input">
        <div class="title">Input</div>
        <pre><div class="test-example-line">2 3</div><div class="test-example-line">  1  2  3</div><div class="test-example-line">  4  5  6</div></pre>
      </div>
      <div class="output">
        <div class="title">Output</div>
        <pre><div class="test-example-line">  1  2  3</div><div class="test-example-line">  4  5  6</div></pre>
      </div>
    </div>
  </div>
  <div class="note">
    <div class="section-title">Note</div>
    <p>Notice the two leading spaces before each row element.</p>
  </div>
</div>
</body>
</html>
"""


def assert_zero_devanagari(text: str) -> None:
    """Assert text contains zero Devanagari Unicode glyphs."""
    matches = DEVANAGARI_REGEX.findall(text)
    assert not matches, f"Found {len(matches)} illegal Devanagari characters: {matches[:10]}"


def assert_branding_present(text_or_pdf: str | Path) -> None:
    """Assert mandatory branding is embedded in text or PDF."""
    if isinstance(text_or_pdf, Path):
        doc = fitz.open(text_or_pdf)
        all_text = " ".join(p.get_text() for p in doc)
        doc.close()
    else:
        all_text = text_or_pdf
    assert "@issparsh" in all_text and "@sumitsingh097" in all_text, (
        f"Mandatory branding '@issparsh @sumitsingh097' missing from artifact."
    )


def assert_iso_a4_pdf(pdf_path: Path) -> None:
    """Assert PDF matches ISO A4 dimensions and has valid structure."""
    doc = fitz.open(pdf_path)
    assert len(doc) >= 1, "PDF has zero pages"
    for page in doc:
        rect = page.rect
        assert abs(rect.width - ISO_A4_WIDTH) < 1.0, f"Page width {rect.width} not ISO A4"
        assert abs(rect.height - ISO_A4_HEIGHT) < 1.0, f"Page height {rect.height} not ISO A4"
    doc.close()
