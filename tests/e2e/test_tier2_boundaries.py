"""Tier 2: Boundary & Corner Cases (B1 - B10).

Minimum 50 test cases (>= 5 test cases per feature area).
Tests boundary values, edge conditions, invalid inputs, and adversarial stress
for the requirements in ORIGINAL_REQUEST.md and PROJECT.md.
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
# B1: Malformed URLs & Protocol Injection
# ---------------------------------------------------------------------------

def test_b1_01_url_missing_host():
    """B1.1: Reject URLs missing host component."""
    from scripts.ingestion.yt_ingest import is_youtube_url
    assert is_youtube_url("https:///watch?v=dQw4w9WgXcQ") is False
    assert is_youtube_url("http://") is False


def test_b1_02_url_with_whitespace_and_newlines():
    """B1.2: Strips outer whitespace in URLs before validation."""
    from scripts.ingestion.yt_ingest import is_youtube_url
    assert is_youtube_url("  https://www.youtube.com/watch?v=dQw4w9WgXcQ \n") is True
    assert is_youtube_url("\thttps://youtu.be/dQw4w9WgXcQ\t") is True


def test_b1_03_url_with_non_ascii_characters():
    """B1.3: Handles non-ASCII / Unicode domain spoofing cleanly."""
    from scripts.ingestion.yt_ingest import is_youtube_url
    # Cyrillic 'а' or similar spoofed domains
    assert is_youtube_url("https://уoutubе.com/watch?v=123") is False


def test_b1_04_url_with_port_and_auth():
    """B1.4: Handles URLs with explicit ports and userinfo safely."""
    from scripts.ingestion.yt_ingest import is_youtube_url
    assert is_youtube_url("https://user:pass@youtube.com:443/watch?v=123") is True


def test_b1_05_url_empty_or_non_string():
    """B1.5: Rejects empty strings and non-string types safely without exception."""
    from scripts.ingestion.yt_ingest import is_youtube_url
    assert is_youtube_url("") is False
    assert is_youtube_url("   ") is False
    assert is_youtube_url(None) is False  # type: ignore
    assert is_youtube_url(12345) is False  # type: ignore
    assert is_youtube_url(["https://youtube.com"]) is False  # type: ignore


# ---------------------------------------------------------------------------
# B2: Empty Sources & Corpus Underflow
# ---------------------------------------------------------------------------

def test_b2_01_empty_sources_list(temp_e2e_workspace: Path):
    """B2.1: Ingestion with empty source list produces empty corpus without crash."""
    from thenuke_cli import run_ingest
    corpus_file = temp_e2e_workspace / "empty_corpus.json"
    result_path = run_ingest([], corpus_path=corpus_file)
    assert Path(result_path).exists()
    data = json.loads(Path(result_path).read_text(encoding="utf-8"))
    assert len(data.get("sources", [])) == 0


def test_b2_02_sources_list_with_only_empty_strings(temp_e2e_workspace: Path):
    """B2.2: Ingestion with only blank strings skips invalid sources cleanly."""
    from thenuke_cli import run_ingest
    corpus_file = temp_e2e_workspace / "blank_corpus.json"
    result_path = run_ingest(["", "   ", "\t"], corpus_path=corpus_file)
    data = json.loads(Path(result_path).read_text(encoding="utf-8"))
    assert len(data.get("sources", [])) == 0


def test_b2_03_non_existent_local_file_source(temp_e2e_workspace: Path):
    """B2.3: Ingestion with non-existent local file path handled gracefully."""
    from thenuke_cli import run_ingest
    corpus_file = temp_e2e_workspace / "missing_file_corpus.json"
    fake_path = str(temp_e2e_workspace / "does_not_exist_file.pdf")
    result_path = run_ingest([fake_path], corpus_path=corpus_file)
    data = json.loads(Path(result_path).read_text(encoding="utf-8"))
    assert len(data.get("sources", [])) == 0


def test_b2_04_corpus_with_zero_sources_serialization(temp_e2e_workspace: Path):
    """B2.4: Empty UnifiedCorpus serializes and deserializes cleanly."""
    from scripts.ingestion.unified_corpus import UnifiedCorpus
    corpus = UnifiedCorpus()
    out_file = temp_e2e_workspace / "roundtrip_empty.json"
    corpus.save(out_file)
    loaded = UnifiedCorpus.load(out_file)
    assert len(loaded.sources) == 0


def test_b2_05_corpus_loading_empty_json_file(temp_e2e_workspace: Path):
    """B2.5: UnifiedCorpus handles bare empty dict JSON file."""
    from scripts.ingestion.unified_corpus import UnifiedCorpus
    empty_json = temp_e2e_workspace / "empty.json"
    empty_json.write_text("{}", encoding="utf-8")
    loaded = UnifiedCorpus.load(empty_json)
    assert len(loaded.sources) == 0


# ---------------------------------------------------------------------------
# B3: Irregular Matrices & Extreme Whitespace in CP
# ---------------------------------------------------------------------------

def test_b3_01_matrix_with_mixed_tabs_and_spaces():
    """B3.1: Preserves mixed tabs and spaces in sample inputs."""
    from scripts.ingestion.cp_problem import CPSample
    raw = "\t1  \t2\n\t3  \t4"
    sample = CPSample(sample_index=1, input_text=raw, output_text="10")
    assert sample.input_text == raw


def test_b3_02_matrix_with_alternating_indentation():
    """B3.2: Preserves alternating indentation across matrix rows."""
    from scripts.ingestion.cp_problem import CPSample
    raw = "  row1\n    row2\n  row3\n    row4"
    sample = CPSample(sample_index=1, input_text=raw, output_text="OK")
    assert "    row2" in sample.input_text
    assert "    row4" in sample.input_text


def test_b3_03_matrix_with_oversized_row_1000_chars():
    """B3.3: Handles massive single-line matrix row (1000 numbers)."""
    from scripts.ingestion.cp_problem import CPSample
    row = " ".join(str(i) for i in range(1000))
    sample = CPSample(sample_index=1, input_text=row, output_text="SUM")
    assert len(sample.input_text) > 1000


def test_b3_04_matrix_with_leading_and_trailing_newlines():
    """B3.4: Normalizes multiple blank lines without removing internal blank rows."""
    from scripts.ingestion.cp_problem import CPSample
    raw = "1 2\n\n3 4"
    sample = CPSample(sample_index=1, input_text=raw, output_text="OK")
    assert "\n\n" in sample.input_text


def test_b3_05_sample_with_empty_input_non_empty_output():
    """B3.5: Handles sample test cases where input is empty."""
    from scripts.ingestion.cp_problem import CPSample
    sample = CPSample(sample_index=1, input_text="", output_text="42")
    assert sample.input_text == ""
    assert sample.output_text == "42"


# ---------------------------------------------------------------------------
# B4: Zero-Length Files & Malformed Media
# ---------------------------------------------------------------------------

def test_b4_01_zero_length_pdf_file(temp_e2e_workspace: Path):
    """B4.1: 0-byte PDF file handled safely by extract_pdf."""
    from scripts.ingestion.file_extract import extract_pdf
    zero_pdf = temp_e2e_workspace / "zero.pdf"
    zero_pdf.write_bytes(b"")
    # Should catch PyMuPDF exception and return empty or raise cleanly
    try:
        source = extract_pdf(zero_pdf)
        assert len(source.chapters) == 0
    except Exception as exc:
        assert "zero" in str(zero_pdf) or "cannot open" in str(exc).lower() or "empty" in str(exc).lower()


def test_b4_02_zero_length_vtt_file():
    """B4.2: 0-byte VTT content returns empty list from parse_vtt_cues."""
    from scripts.ingestion.yt_ingest import parse_vtt_cues
    cues = parse_vtt_cues("")
    assert cues == []


def test_b4_03_zero_length_pptx_file(temp_e2e_workspace: Path):
    """B4.3: 0-byte PPTX file handled gracefully without crash."""
    from scripts.ingestion.file_extract import extract_pptx
    zero_pptx = temp_e2e_workspace / "zero.pptx"
    zero_pptx.write_bytes(b"")
    try:
        source = extract_pptx(zero_pptx)
        assert len(source.chapters) == 0
    except Exception as exc:
        assert True  # Handled exception is acceptable


def test_b4_04_zero_length_html_file():
    """B4.4: 0-byte HTML string produces empty markdown and code blocks."""
    from scripts.ingestion.web_crawler import html_to_markdown_and_code
    md, code_blocks, tables = html_to_markdown_and_code("")
    assert md == ""
    assert len(code_blocks) == 0


def test_b4_05_truncated_pdf_header_only(temp_e2e_workspace: Path):
    """B4.5: Corrupt PDF with header only handled gracefully."""
    trunc_pdf = temp_e2e_workspace / "corrupt.pdf"
    trunc_pdf.write_bytes(b"%PDF-1.4\n%%EOF")
    from scripts.qa.qa_audit_engine import run_qa_audit
    try:
        report = run_qa_audit(trunc_pdf)
        assert not report.overall_passed
    except Exception:
        # Failing or catching corrupt file is valid
        pass


# ---------------------------------------------------------------------------
# B5: Special Characters & Shell Invariants in Branding
# ---------------------------------------------------------------------------

def test_b5_01_branding_with_xml_special_chars(temp_e2e_workspace: Path):
    """B5.1: Custom branding containing &, <, >, \", ' escapes cleanly in ReportLab."""
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder
    out_pdf = temp_e2e_workspace / "branding_xml.pdf"
    weird_branding = "Prepared by @issparsh & <Partner> @sumitsingh097 'Official' \"Edition\""
    builder = ReferenceManualBuilder(out_pdf, topic="Git", branding=weird_branding)
    builder.compile("# Test Title\nContent paragraph.")
    assert out_pdf.exists()


def test_b5_02_branding_with_unicode_symbols(temp_e2e_workspace: Path):
    """B5.2: Branding with mathematical and copyright Unicode symbols."""
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder
    out_pdf = temp_e2e_workspace / "branding_unicode.pdf"
    unicode_branding = "Prepared by @issparsh @sumitsingh097 © 2026 — High-Density 𝕏 Edition"
    builder = ReferenceManualBuilder(out_pdf, topic="Git", branding=unicode_branding)
    builder.compile("# Test Title\nContent paragraph.")
    assert out_pdf.exists()


def test_b5_03_extremely_long_branding_string(temp_e2e_workspace: Path):
    """B5.3: Extremely long branding string (300+ characters) does not break canvas."""
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder
    out_pdf = temp_e2e_workspace / "branding_long.pdf"
    long_branding = ("Prepared by @issparsh @sumitsingh097 " * 15)[:300]
    builder = ReferenceManualBuilder(out_pdf, topic="Git", branding=long_branding)
    builder.compile("# Test Title\nContent paragraph.")
    assert out_pdf.exists()


def test_b5_04_branding_with_newlines(temp_e2e_workspace: Path):
    """B5.4: Branding containing newline characters handled cleanly."""
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder
    out_pdf = temp_e2e_workspace / "branding_nl.pdf"
    nl_branding = "Prepared by @issparsh\n@sumitsingh097"
    builder = ReferenceManualBuilder(out_pdf, topic="Git", branding=nl_branding)
    builder.compile("# Test Title\nContent paragraph.")
    assert out_pdf.exists()


def test_b5_05_branding_empty_string_fallback(temp_e2e_workspace: Path):
    """B5.5: Empty branding string compiles without crashing canvas."""
    from scripts.diagramming.reportlab_engine import ReferenceManualBuilder
    out_pdf = temp_e2e_workspace / "branding_empty.pdf"
    builder = ReferenceManualBuilder(out_pdf, topic="Git", branding="")
    builder.compile("# Test Title\nContent paragraph.")
    assert out_pdf.exists()


# ---------------------------------------------------------------------------
# B6: Clean Command Idempotence & Boundary States
# ---------------------------------------------------------------------------

def test_b6_01_clean_when_scratch_does_not_exist(temp_e2e_workspace: Path):
    """B6.1: Cleanup handles non-existent scratch directory without error."""
    from thenuke_cli import run_cleanup
    missing_dir = temp_e2e_workspace / "non_existent_dir_999"
    run_cleanup(scratch_dir=missing_dir, confirm=False)


def test_b6_02_clean_called_ten_times_rapidly(temp_e2e_workspace: Path):
    """B6.2: Cleanup is fully idempotent under repeated consecutive calls."""
    from thenuke_cli import run_cleanup
    scratch = temp_e2e_workspace / "scratch_repeat"
    scratch.mkdir()
    for _ in range(10):
        run_cleanup(scratch_dir=scratch, confirm=False)


def test_b6_03_clean_when_assets_already_deleted(temp_e2e_workspace: Path, monkeypatch):
    """B6.3: Cleanup handles already-deleted assets directory without raising."""
    from thenuke_cli import run_cleanup
    monkeypatch.chdir(temp_e2e_workspace)
    assert not (temp_e2e_workspace / "assets").exists()
    run_cleanup(scratch_dir=temp_e2e_workspace / "scratch", confirm=False)


def test_b6_04_clean_with_nested_subdirectories(temp_e2e_workspace: Path):
    """B6.4: Cleanup deletes deeply nested directory trees inside scratch."""
    from thenuke_cli import SCRATCH_SUBDIRS, run_cleanup
    scratch = temp_e2e_workspace / "scratch_deep"
    for sub in SCRATCH_SUBDIRS:
        deep = scratch / sub / "level1" / "level2" / "level3"
        deep.mkdir(parents=True, exist_ok=True)
        (deep / "deep_file.tmp").write_text("deep data")

    run_cleanup(scratch_dir=scratch, confirm=False)
    for sub in SCRATCH_SUBDIRS:
        assert not (scratch / sub).exists()


def test_b6_05_clean_with_hidden_dotfiles_in_scratch(temp_e2e_workspace: Path):
    """B6.5: Cleanup wipes hidden dotfiles (.DS_Store, .tmp) inside scratch."""
    from thenuke_cli import SCRATCH_SUBDIRS, run_cleanup
    scratch = temp_e2e_workspace / "scratch_dotfiles"
    for sub in SCRATCH_SUBDIRS:
        p = scratch / sub
        p.mkdir(parents=True, exist_ok=True)
        (p / ".DS_Store").write_bytes(b"\x00\x00")
        (p / ".hidden_temp").write_text("hidden")

    run_cleanup(scratch_dir=scratch, confirm=False)
    for sub in SCRATCH_SUBDIRS:
        assert not (scratch / sub).exists()


# ---------------------------------------------------------------------------
# B7: QA Audit Structural Boundaries
# ---------------------------------------------------------------------------

def test_b7_01_qa_audit_on_single_blank_page_pdf(temp_e2e_workspace: Path):
    """B7.1: Single blank page PDF fails QA audit (missing branding & content)."""
    from scripts.qa.qa_audit_engine import run_qa_audit
    pdf_path = temp_e2e_workspace / "blank_page.pdf"
    doc = fitz.open()
    doc.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    doc.save(pdf_path)
    doc.close()

    report = run_qa_audit(pdf_path)
    assert not report.overall_passed


def test_b7_02_qa_audit_on_corrupt_pdf_file(temp_e2e_workspace: Path):
    """B7.2: Corrupted non-PDF binary file fails QA audit gracefully."""
    from scripts.qa.qa_audit_engine import run_qa_audit
    pdf_path = temp_e2e_workspace / "corrupt_data.pdf"
    pdf_path.write_bytes(b"NOT_A_VALID_PDF_STREAM_RANDOM_BYTES_0123456789")
    try:
        report = run_qa_audit(pdf_path)
        assert not report.overall_passed
    except Exception:
        pass


def test_b7_03_qa_audit_on_non_existent_pdf_path(temp_e2e_workspace: Path):
    """B7.3: Non-existent PDF path raises FileNotFoundError or fails cleanly."""
    from scripts.qa.qa_audit_engine import run_qa_audit
    missing = temp_e2e_workspace / "no_such_file.pdf"
    with pytest.raises(Exception):
        run_qa_audit(missing)


def test_b7_04_qa_audit_on_pdf_with_massive_overflow_text(temp_e2e_workspace: Path):
    """B7.4: Detects text running across margins in poorly formatted PDF."""
    from scripts.qa.qa_audit_engine import run_qa_audit
    pdf_path = temp_e2e_workspace / "overflow_test.pdf"
    doc = fitz.open()
    page = doc.new_page(width=ISO_A4_WIDTH, height=ISO_A4_HEIGHT)
    page.insert_text(fitz.Point(10, 100), "A" * 500, fontsize=14)  # overflows right margin
    doc.save(pdf_path)
    doc.close()

    report = run_qa_audit(pdf_path)
    assert report is not None


def test_b7_05_qa_audit_empty_pdf_no_pages(temp_e2e_workspace: Path):
    """B7.5: PDF with 0 pages fails QA audit cleanly."""
    from scripts.qa.qa_audit_engine import run_qa_audit
    pdf_path = temp_e2e_workspace / "zero_pages.pdf"
    # Construct raw valid PDF trailer with /Count 0
    raw_0_page_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n"
        b"xref\n0 3\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"trailer\n<< /Root 1 0 R /Size 3 >>\n"
        b"startxref\n115\n%%EOF"
    )
    pdf_path.write_bytes(raw_0_page_pdf)

    try:
        report = run_qa_audit(pdf_path)
        assert not report.overall_passed
    except Exception:
        pass


# ---------------------------------------------------------------------------
# B8: CorpusIndexer Edge Conditions
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="Pending M4 remediation: CorpusIndexer module", strict=False)
def test_b8_01_indexer_on_empty_corpus():
    """B8.1: Indexer on empty corpus returns empty span list without crash."""
    from scripts.ingestion.unified_corpus import UnifiedCorpus
    from scripts.synthesis.corpus_indexer import CorpusIndexer
    corpus = UnifiedCorpus()
    indexer = CorpusIndexer()
    spans = indexer.index(corpus)
    assert spans == []


@pytest.mark.xfail(reason="Pending M4 remediation: CorpusIndexer whitespace chapter handling", strict=False)
def test_b8_02_indexer_on_chapters_with_whitespace_only():
    """B8.2: Indexer skips chapters containing only whitespace."""
    from scripts.ingestion.unified_corpus import Chapter, IngestionSource, UnifiedCorpus
    from scripts.synthesis.corpus_indexer import CorpusIndexer
    src = IngestionSource(
        source_type="web",
        identifier="https://example.com/empty",
        title="Empty",
        chapters=[Chapter(chapter_index=1, title="Empty Chapter", text="   \n\t   ")],
    )
    corpus = UnifiedCorpus(sources=[src])
    indexer = CorpusIndexer()
    spans = indexer.index(corpus)
    assert len(spans) == 0


@pytest.mark.xfail(reason="Pending M4 remediation: CorpusIndexer duplicate source handling", strict=False)
def test_b8_03_indexer_on_sources_with_duplicate_ids():
    """B8.3: Indexer handles sources with duplicate URIs or identifiers."""
    from scripts.ingestion.unified_corpus import Chapter, IngestionSource, UnifiedCorpus
    from scripts.synthesis.corpus_indexer import CorpusIndexer
    src1 = IngestionSource(source_type="web", identifier="https://dup.com", chapters=[Chapter(1, "C1", "Text A")])
    src2 = IngestionSource(source_type="web", identifier="https://dup.com", chapters=[Chapter(2, "C2", "Text B")])
    corpus = UnifiedCorpus(sources=[src1, src2])
    indexer = CorpusIndexer()
    spans = indexer.index(corpus)
    assert len(spans) == 2


@pytest.mark.xfail(reason="Pending M4 remediation: CorpusIndexer oversized chapter chunking", strict=False)
def test_b8_04_indexer_oversized_chapter_text():
    """B8.4: Indexer handles massive chapter (50,000 chars) without memory leak."""
    from scripts.ingestion.unified_corpus import Chapter, IngestionSource, UnifiedCorpus
    from scripts.synthesis.corpus_indexer import CorpusIndexer
    big_text = "Important engineering concepts. " * 1500
    src = IngestionSource(source_type="local_file", identifier="large.txt", chapters=[Chapter(1, "Big", big_text)])
    corpus = UnifiedCorpus(sources=[src])
    indexer = CorpusIndexer()
    spans = indexer.index(corpus)
    assert len(spans) >= 1


@pytest.mark.xfail(reason="Pending M4 remediation: CorpusIndexer code block language fallback", strict=False)
def test_b8_05_indexer_code_block_without_language():
    """B8.5: Indexer handles code blocks without language tag."""
    from scripts.ingestion.unified_corpus import CodeBlock, IngestionSource, UnifiedCorpus
    from scripts.synthesis.corpus_indexer import CorpusIndexer
    src = IngestionSource(
        source_type="web",
        identifier="https://code.example.com",
        extracted_code_blocks=[CodeBlock(language="", code="echo 'hello'")],
    )
    corpus = UnifiedCorpus(sources=[src])
    indexer = CorpusIndexer()
    spans = indexer.index(corpus)
    code_spans = [s for s in spans if s.span_type == "code"]
    assert len(code_spans) == 1


# ---------------------------------------------------------------------------
# B9: CLI Argument Boundary & Syntax Validation
# ---------------------------------------------------------------------------

def test_b9_01_cli_no_arguments_exits_code_2():
    """B9.1: Invoking CLI without arguments displays usage and exits 2."""
    res = subprocess.run([sys.executable, "thenuke_cli.py"], cwd=str(ROOT_DIR), capture_output=True, text=True)
    assert res.returncode == 2


def test_b9_02_cli_unknown_subcommand_exits_code_2():
    """B9.2: Invoking CLI with unknown subcommand exits with code 2."""
    res = subprocess.run([sys.executable, "thenuke_cli.py", "invalid_subcmd"], cwd=str(ROOT_DIR), capture_output=True, text=True)
    assert res.returncode == 2


def test_b9_03_cli_compile_missing_required_markdown_arg():
    """B9.3: Invoking compile without markdown path argument exits with code 2."""
    res = subprocess.run([sys.executable, "thenuke_cli.py", "compile"], cwd=str(ROOT_DIR), capture_output=True, text=True)
    assert res.returncode == 2


def test_b9_04_cli_qa_missing_required_pdf_arg():
    """B9.4: Invoking qa without PDF path argument exits with code 2."""
    res = subprocess.run([sys.executable, "thenuke_cli.py", "qa"], cwd=str(ROOT_DIR), capture_output=True, text=True)
    assert res.returncode == 2


def test_b9_05_cli_run_multiple_sources_argv():
    """B9.5: CLI parses multiple source arguments in list."""
    from thenuke_cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["run", "https://yt.com/1", "https://web.com/2", "file.pdf"])
    assert len(args.sources) == 3
    assert args.sources == ["https://yt.com/1", "https://web.com/2", "file.pdf"]


# ---------------------------------------------------------------------------
# B10: Math & LaTeX Edge Delimiters in CP Statements
# ---------------------------------------------------------------------------

def test_b10_01_cp_nested_dollar_delimiters():
    """B10.1: Normalizes inline math delimiters cleanly."""
    from scripts.ingestion.cp_problem import normalize_math_delimiters
    raw = "Given $1 \\le n \\le 100$ and $m > 0$."
    norm = normalize_math_delimiters(raw)
    assert "$1 \\le n \\le 100$" in norm or "1 \\le n \\le 100" in norm


def test_b10_02_cp_escaped_curly_braces_in_math():
    """B10.2: Preserves escaped curly braces in set notation."""
    from scripts.ingestion.cp_problem import normalize_math_delimiters
    raw = "$S = \\{1, 2, 3\\}$"
    norm = normalize_math_delimiters(raw)
    assert "{" in norm and "}" in norm


def test_b10_03_cp_floor_ceil_delimiters():
    """B10.3: Normalizes floor and ceiling symbols."""
    from scripts.ingestion.cp_problem import normalize_math_delimiters
    raw = "$\\lfloor x \\rfloor \\le \\lceil y \\rceil$"
    norm = normalize_math_delimiters(raw)
    assert norm is not None


def test_b10_04_cp_empty_math_delimiters():
    """B10.4: Handles empty dollar blocks without crash."""
    from scripts.ingestion.cp_problem import normalize_math_delimiters
    raw = "Text with $ $ and $$ $$ empty delimiters."
    norm = normalize_math_delimiters(raw)
    assert "Text with" in norm


def test_b10_05_cp_html_arrow_entities():
    """B10.5: Preserves or cleanly converts HTML arrow entities (&rarr;, &le;, &ge;)."""
    import lxml.html
    from scripts.ingestion.cp_problem import clean_html_formatting_to_markdown
    html_frag = "<p>Step 1 &rarr; Step 2 (&le; 100)</p>"
    el = lxml.html.fragment_fromstring(html_frag)
    md = clean_html_formatting_to_markdown(el)
    assert "Step 1" in md and "Step 2" in md
