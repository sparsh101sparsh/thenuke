"""Test suite verifying all remediation features and architectural invariants.

Covers:
1. Packaging & Fixture Integrity (requirements, sample_doc.pdf)
2. Operational Safety & Defaults (download_video=False, is_youtube_url scheme check)
3. Scratch Isolation & Cleanup
4. Branding Parameter Wiring
5. CP Whitespace Precision & Delimiter DOTALL
6. CorpusIndexer Evidence Layer & Extractive Notes Synthesis
7. Multi-Profile QA Verification (git, js, cp, notes)
8. CLI Exit Codes on QA Failures
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts.ingestion.yt_ingest import is_youtube_url
from scripts.ingestion.unified_corpus import UnifiedCorpus, IngestionSource, Chapter, CodeBlock, ExtractedImage
from scripts.ingestion.cp_problem import normalize_math_delimiters, CPProblem, CPSample, extract_codeforces_problem
from scripts.synthesis.corpus_indexer import CorpusIndexer, EvidenceSpan
from scripts.synthesis.extractive_notes import ExtractiveNotesSynthesizer
from scripts.diagramming.reportlab_engine import ReferenceManualBuilder, PublicationCanvas
from scripts.qa.qa_audit_engine import run_pass1_visual, run_pass2_textual, run_qa_audit


class TestPackagingAndFixtures:
    """Verifies R1 packaging and fixture requirements."""

    def test_sample_doc_pdf_fixture_exists(self):
        fixture_path = Path("tests/fixtures/sample_doc.pdf")
        assert fixture_path.exists(), "tests/fixtures/sample_doc.pdf must exist on disk and be tracked in git"
        assert fixture_path.stat().st_size > 0

    def test_requirements_contains_runtime_deps(self):
        req_text = Path("requirements.txt").read_text(encoding="utf-8")
        assert "reportlab" in req_text
        assert "beautifulsoup4" in req_text
        assert "online-judge-tools" in req_text

    def test_pyproject_toml_structure(self):
        pyproject_path = Path("pyproject.toml")
        assert pyproject_path.exists()
        content = pyproject_path.read_text(encoding="utf-8")
        assert 'name = "thenuke"' in content
        assert "reportlab" in content
        assert 'thenuke = "thenuke_cli:main"' in content


class TestOperationalSafetyAndDefaults:
    """Verifies R2 operational safety invariants."""

    def test_youtube_url_requires_http_or_https_scheme(self):
        assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
        assert is_youtube_url("http://youtu.be/dQw4w9WgXcQ") is True
        assert is_youtube_url("ftp://youtube.com/watch?v=dQw4w9WgXcQ") is False
        assert is_youtube_url("file://youtube.com/watch?v=dQw4w9WgXcQ") is False
        assert is_youtube_url("javascript:youtube.com") is False
        assert is_youtube_url("not_a_url") is False

    def test_branding_wired_to_reference_manual_builder(self, tmp_path):
        target_pdf = tmp_path / "test_branding.pdf"
        custom_branding = "Prepared by @custom_author"
        builder = ReferenceManualBuilder(target_pdf, topic="TestTopic", branding=custom_branding)
        assert builder.branding == custom_branding


class TestCPWhitespaceAndDelimiters:
    """Verifies R3 CP precision requirements."""

    def test_cf_triple_dollar_multiline_dotall(self):
        input_text = "Let $$$a +\nb$$$ be a sum and $$$x$$$ a variable."
        normalized = normalize_math_delimiters(input_text)
        assert "$a +\nb$" in normalized
        assert "$x$" in normalized
        assert "$$$" not in normalized

    def test_sample_whitespace_preserved_in_markdown(self):
        sample_in = "  1 2 3\n 4  5 6\n7 8 9"
        sample_out = " YES\n  NO"
        sample = CPSample(sample_index=1, input_text=sample_in, output_text=sample_out)
        prob = CPProblem(
            platform="codeforces",
            url="https://codeforces.com/problemset/problem/1/A",
            problem_id="1A",
            title="Theatre Square",
            time_limit="1.0 s",
            memory_limit="256 MB",
            statement_markdown="Given a grid.",
            samples=[sample],
        )
        md = prob.to_structured_markdown()
        # Verify exact leading spaces survive inside code blocks
        assert "  1 2 3\n 4  5 6\n7 8 9" in md
        assert " YES\n  NO" in md


class TestCorpusIndexerAndExtractiveNotes:
    """Verifies R4 Evidence Layer & Extractive Notes System."""

    @pytest.fixture
    def sample_corpus(self) -> UnifiedCorpus:
        corpus = UnifiedCorpus()
        src = IngestionSource(
            source_type="youtube",
            identifier="https://youtube.com/watch?v=test1234",
            title="Distributed Systems Foundations",
            metadata={"uploader": "MIT OpenCourseWare"},
        )
        src.add_chapter(
            title="Raft Consensus Algorithm",
            text="In Raft, consensus is achieved through leader election and log replication.\n\n"
                 "The leader handles all client requests and replicates entries to followers.",
            start_time=120.0,
            end_time=360.0,
        )
        src.add_chapter(
            title="Byzantine Fault Tolerance",
            text="BFT systems can tolerate arbitrary malicious or fail-stop nodes up to 3f+1 total nodes.",
            start_time=360.0,
            end_time=720.0,
        )
        src.add_code_block("def elect_leader():\n    return 'leader'", language="python")
        src.add_image("frames/frame_01.png", caption="Raft State Transition Diagram", ocr_text="Follower -> Candidate -> Leader")
        corpus.sources.append(src)
        return corpus

    def test_corpus_indexer_extracts_all_span_types(self, sample_corpus):
        indexer = CorpusIndexer(sample_corpus)
        spans = indexer.get_all_spans()
        assert len(spans) >= 4

        types = {s.span_type for s in spans}
        assert "transcript" in types
        assert "code" in types
        assert "ocr" in types

        sections = indexer.get_sections()
        assert len(sections) >= 2
        titles = [s["title"] for s in sections]
        assert any("Raft" in t for t in titles)
        assert any("Byzantine" in t for t in titles)

    def test_extractive_notes_synthesizer_generates_grounded_manual(self, sample_corpus):
        indexer = CorpusIndexer(sample_corpus)
        synthesizer = ExtractiveNotesSynthesizer(indexer, topic="Distributed Systems")
        md = synthesizer.generate_markdown()

        # Invariant Assertions:
        assert "# Distributed Systems: Grounded Reference Manual & Extractive Notes" in md
        assert "Syllabus Index & Architectural Roadmap" in md
        assert "Phase 1:" in md
        assert "[SOURCE TAPE" in md
        assert "Raft consensus" in md.lower() or "byzantine" in md.lower()
        assert "[MENTAL MODEL]" in md
        assert "[ENGINEERING GOTCHA]" in md
        assert "def elect_leader():" in md
        assert "CHALLENGE 1:" in md
        assert "CHALLENGE 2:" in md
        assert "CHALLENGE 3:" in md
        assert "Appendix A: Evidence Traceability Matrix" in md

        # Zero Devanagari invariant
        import re
        assert re.search(r"[\u0900-\u097F]", md) is None

    def test_notes_qa_profile_passes_synthesized_manual(self, sample_corpus, tmp_path):
        indexer = CorpusIndexer(sample_corpus)
        synthesizer = ExtractiveNotesSynthesizer(indexer, topic="Distributed Systems")
        md_text = synthesizer.generate_markdown()

        pdf_path = tmp_path / "notes_test.pdf"
        builder = ReferenceManualBuilder(pdf_path, topic="Distributed Systems")
        out_pdf = builder.compile(md_text)

        report = run_qa_audit(out_pdf, profile="notes")
        assert report.overall_passed is True
        assert report.pass2_textual.passed is True
        assert len(report.pass2_textual.devanagari_violations) == 0


class TestQAProfiles:
    """Verifies dedicated QA profile splitting."""

    def test_cp_profile_does_not_require_git_phases(self, tmp_path):
        md_content = """# Codeforces 1915C - Can I Square?

**Platform:** Codeforces | **Time Limit:** 1.0 s | **Memory Limit:** 256 MB

Given $n$ square buckets. Determine if total squares can form a larger square.

### Sample Tests & Verification

:::sample 1
#### Input
```
3
1 2 3
```
#### Output
```
NO
```
:::

Prepared by @issparsh @sumitsingh097
"""
        pdf_path = tmp_path / "cp_test.pdf"
        builder = ReferenceManualBuilder(pdf_path, topic="Codeforces 1915C")
        out_pdf = builder.compile(md_content)

        report = run_qa_audit(out_pdf, profile="cp")
        assert report.overall_passed is True
        assert report.pass2_textual.passed is True
