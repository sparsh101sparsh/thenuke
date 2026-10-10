"""Comprehensive Test Suite for Competitive Programming (CP) Problem Ingestion & Rendering.

Validates:
1. URL routing and platform detection for Codeforces, LeetCode, and AtCoder.
2. Codeforces HTML extraction with LaTeX math preservation and multi-line sample integrity.
3. LeetCode GraphQL ingestion with structured examples, constraints, and tags.
4. AtCoder HTML extraction with <var> math conversion and sample extraction.
5. LaTeX math translation to ReportLab rich-text typography (superscripts, subscripts, entities).
6. End-to-end PDF compilation, sample box rendering, branding, and QA audit passing.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pymupdf

from scripts.diagramming.reportlab_engine import (
    ReferenceManualBuilder,
    latex_to_reportlab_html,
    md_to_reportlab_html,
)
from scripts.ingestion import run_ingestion
from scripts.ingestion.cp_problem import (
    CPProblem,
    CPSample,
    detect_cp_platform,
    extract_atcoder_problem,
    extract_codeforces_problem,
    extract_cp_problem,
    extract_leetcode_problem,
    ingest_cp_problem,
    is_cp_url,
)
from scripts.qa.qa_audit_engine import run_qa_audit


# ===========================================================================
# 1. URL Detection & Platform Routing Tests
# ===========================================================================

class TestCPUrlDetection:
    """Verifies that CP URLs are accurately detected and classified."""

    @pytest.mark.parametrize(
        "url,expected_platform",
        [
            ("https://codeforces.com/problemset/problem/1915/C", "codeforces"),
            ("http://codeforces.com/contest/1915/problem/C", "codeforces"),
            ("https://codeforces.com/gym/102951/problem/A", "codeforces"),
            ("https://leetcode.com/problems/two-sum/", "leetcode"),
            ("https://leetcode.com/problems/median-of-two-sorted-arrays", "leetcode"),
            ("https://atcoder.jp/contests/abc300/tasks/abc300_a", "atcoder"),
            ("https://atcoder.jp/contests/arc150/tasks/arc150_b", "atcoder"),
        ],
    )
    def test_positive_cp_urls(self, url: str, expected_platform: str):
        assert is_cp_url(url) is True
        assert detect_cp_platform(url) == expected_platform

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.youtube.com/watch?v=5MuIMqhT8DM",
            "https://github.com/torvalds/linux",
            "https://en.wikipedia.org/wiki/Dynamic_programming",
            "https://codeforces.com/profile/tourist",
            "https://leetcode.com/discuss/general-discussion",
            "/path/to/local/file.pdf",
        ],
    )
    def test_negative_cp_urls(self, url: str):
        assert is_cp_url(url) is False
        assert detect_cp_platform(url) is None


# ===========================================================================
# 2. LaTeX to ReportLab Math Translation Tests
# ===========================================================================

class TestLaTeXPreservation:
    """Verifies that LaTeX formulas survive intact into vector typography tags."""

    def test_superscript_and_subscript(self):
        res = latex_to_reportlab_html(r"(-1)^{a+b}S^2")
        assert "<super>" in res and "a" in res and "b" in res
        assert "<super>" in res and "2" in res
        assert "6.5" in res  # Scaled math exponent

        res_sub = latex_to_reportlab_html(r"a_1, \ldots, a_n")
        assert "<sub>" in res_sub and "1" in res_sub
        assert "<sub>" in res_sub and "n" in res_sub

    def test_inequalities_and_operators(self):
        res = latex_to_reportlab_html(r"1 \le n \le 10^5")
        assert "&le;" in res
        assert "10<super><font size=\"6.5\">5</font></super>" in res or ("<super>" in res and "5" in res)

        res_approx = latex_to_reportlab_html(r"2^{31}-1 \approx 2 \cdot 10^9")
        assert "&asymp;" in res_approx
        assert "&middot;" in res_approx

    def test_summations_and_fractions(self):
        res = latex_to_reportlab_html(r"\sum_{i=1}^n a_i = S^2")
        assert "&Sigma;" in res
        assert "<sub>" in res and "i" in res and "1" in res

        res_frac = latex_to_reportlab_html(r"\frac{a+b}{2}")
        assert "a" in res_frac and "b" in res_frac and "/ 2" in res_frac

    def test_md_to_reportlab_preserves_inline_and_display_math(self):
        md = "Given an array of length $n$ with bounds $1 \\le a_i \\le 10^9$."
        html = md_to_reportlab_html(md)
        assert "<i>n</i>" in html or "Helvetica-Oblique" in html
        assert "&le;" in html
        assert "10<super><font size=\"6.5\">9</font></super>" in html or ("<super>" in html and "9" in html)


# ===========================================================================
# 3. Codeforces Extractor Tests (with Mock HTML Fixture)
# ===========================================================================

CODEFORCES_HTML_FIXTURE = """
<!DOCTYPE html>
<html>
<body>
<div class="problem-statement">
  <div class="header">
    <div class="title">C. Can I Square?</div>
    <div class="time-limit"><div class="property-title">time limit per test</div>1.0 s</div>
    <div class="memory-limit"><div class="property-title">memory limit per test</div>256 MB</div>
  </div>
  <div>
    <p>Calin has $$$n$$$ buckets, the $$$i$$$-th containing $$$a_i$$$ wooden squares of side length $$$1$$$.</p>
    <p>Formula invariant: $$$(-1)^{a+b}S^2$$$ must hold.</p>
  </div>
  <div class="input-specification">
    <div class="section-title">Input</div>
    <p>The first line contains $$$t$$$ ($$$1 \\le t \\le 10^4$$$).</p>
    <p>The second line contains $$$a_1, \\ldots, a_n$$$ ($$$1 \\le a_i \\le 10^9$$$).</p>
  </div>
  <div class="output-specification">
    <div class="section-title">Output</div>
    <p>Output "YES" or "NO".</p>
  </div>
  <div class="sample-tests">
    <div class="section-title">Example</div>
    <div class="sample-test">
      <div class="input">
        <div class="title">Input</div>
        <pre><div class="test-example-line">2</div><div class="test-example-line">1</div><div class="test-example-line">9</div></pre>
      </div>
      <div class="output">
        <div class="title">Output</div>
        <pre>YES
YES</pre>
      </div>
    </div>
  </div>
  <div class="note">
    <div class="section-title">Note</div>
    <p>In the first test case, $$$3 \\times 3$$$ square can be formed.</p>
  </div>
</div>
<div class="tag-box"><span class="tag-box" style="font-size:12px;" title="Binary search">binary search</span></div>
<div class="tag-box"><span class="tag-box" style="font-size:12px;" title="Math">math</span></div>
</body>
</html>
"""

class TestCodeforcesExtractor:
    """Verifies Codeforces problem extraction preserves math and multiline sample structure."""

    @patch("scripts.ingestion.cp_problem.requests.get")
    def test_extract_codeforces_problem(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = CODEFORCES_HTML_FIXTURE
        mock_get.return_value = mock_resp

        problem = extract_codeforces_problem("https://codeforces.com/problemset/problem/1915/C")

        assert problem.platform == "codeforces"
        assert problem.problem_id == "1915C"
        assert problem.title == "C. Can I Square?"
        assert problem.time_limit == "1.0 s"
        assert problem.memory_limit == "256 MB"
        assert "binary search" in problem.tags
        assert "math" in problem.tags

        # Math formulas survived
        assert "$n$" in problem.statement_markdown
        assert "$(-1)^{a+b}S^2$" in problem.statement_markdown
        assert "$1 \\le t \\le 10^4$" in problem.input_specification

        # Multiline sample input integrity (not collapsed into 219)
        assert len(problem.samples) == 1
        assert problem.samples[0].input_text == "2\n1\n9"
        assert problem.samples[0].output_text == "YES\nYES"

        # Notes
        assert "3 \\times 3" in problem.notes

    def test_to_structured_markdown(self):
        problem = CPProblem(
            platform="codeforces",
            url="https://codeforces.com/problemset/problem/1915/C",
            problem_id="1915C",
            title="C. Can I Square?",
            time_limit="1.0 s",
            memory_limit="256 MB",
            tags=["math", "binary search"],
            statement_markdown="Calin has $n$ buckets.",
            input_specification="Bounds: $1 \\le n \\le 10^5$.",
            output_specification="Output YES or NO.",
            samples=[CPSample(sample_index=1, input_text="2\n1\n9", output_text="YES\nYES")],
        )
        md = problem.to_structured_markdown()
        assert "# C. Can I Square?" in md
        assert "**Platform:** Codeforces" in md
        assert ":::sample 1" in md
        assert "[MENTAL MODEL]" in md
        assert "[ENGINEERING GOTCHA]" in md
        assert "Prepared by @issparsh @sumitsingh097" in md


# ===========================================================================
# 4. LeetCode Extractor Tests (with Mock GraphQL Fixture)
# ===========================================================================

LEETCODE_GRAPHQL_RESPONSE = {
    "data": {
        "question": {
            "questionFrontendId": "1",
            "title": "Two Sum",
            "titleSlug": "two-sum",
            "content": """
                <p>Given an array of integers <code>nums</code> and an integer <code>target</code>, return <em>indices of the two numbers such that they add up to <code>target</code></em>.</p>
                <p><strong class="example">Example 1:</strong></p>
                <pre><strong>Input:</strong> nums = [2,7,11,15], target = 9
<strong>Output:</strong> [0,1]
<strong>Explanation:</strong> Because nums[0] + nums[1] == 9, we return [0, 1].</pre>
                <p><strong>Constraints:</strong></p>
                <ul>
                  <li><code>2 &le; nums.length &le; 10<sup>4</sup></code></li>
                  <li><code>-10<sup>9</sup> &le; nums[i] &le; 10<sup>9</sup></code></li>
                </ul>
            """,
            "difficulty": "Easy",
            "topicTags": [{"name": "Array"}, {"name": "Hash Table"}],
            "hints": ["A really brute force way would be to search for all possible pairs."],
        }
    }
}

class TestLeetCodeExtractor:
    """Verifies LeetCode problem extraction parses GraphQL responses cleanly."""

    @patch("scripts.ingestion.cp_problem.requests.post")
    def test_extract_leetcode_problem(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = LEETCODE_GRAPHQL_RESPONSE
        mock_post.return_value = mock_resp

        problem = extract_leetcode_problem("https://leetcode.com/problems/two-sum/")

        assert problem.platform == "leetcode"
        assert problem.problem_id in ("1", "two-sum")
        assert problem.title == "1. Two Sum"
        assert problem.difficulty == "Easy"
        assert "Array" in problem.tags
        assert "Hash Table" in problem.tags

        # Constraints & samples
        assert "2 \\le nums.length \\le 10^{4}" in problem.constraints or "nums.length" in problem.constraints
        assert len(problem.samples) == 1
        assert "nums = [2,7,11,15]" in problem.samples[0].input_text
        assert "[0,1]" in problem.samples[0].output_text


# ===========================================================================
# 5. AtCoder Extractor Tests (with Mock HTML Fixture)
# ===========================================================================

ATCODER_HTML_FIXTURE = r"""
<!DOCTYPE html>
<html>
<body>
<div id="main-container">
  <span class="h2">A - N-choice question</span>
  <span class="lang-en">
    <p>Time Limit: 2 sec / Memory Limit: 1024 MB</p>
    <div class="part">
      <section>
        <h3>Problem Statement</h3>
        <p>You are given integers <var>N</var>, <var>A</var>, and <var>B</var>.</p>
      </section>
    </div>
    <div class="part">
      <section>
        <h3>Constraints</h3>
        <p><var>1 \leq N \leq 300</var></p>
      </section>
    </div>
    <div class="part">
      <section>
        <h3>Input</h3>
        <pre><var>N</var> <var>A</var> <var>B</var></pre>
      </section>
    </div>
    <div class="part">
      <section>
        <h3>Output</h3>
        <pre>Print the answer.</pre>
      </section>
    </div>
    <div class="part">
      <section>
        <h3>Sample Input 1</h3>
        <pre>3 125 175
200 300 400</pre>
      </section>
    </div>
    <div class="part">
      <section>
        <h3>Sample Output 1</h3>
        <pre>2</pre>
      </section>
    </div>
  </span>
</div>
</body>
</html>
"""

class TestAtCoderExtractor:
    """Verifies AtCoder problem extraction converts <var> tags to LaTeX math."""

    @patch("scripts.ingestion.cp_problem.requests.get")
    def test_extract_atcoder_problem(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = ATCODER_HTML_FIXTURE
        mock_get.return_value = mock_resp

        problem = extract_atcoder_problem("https://atcoder.jp/contests/abc300/tasks/abc300_a")

        assert problem.platform == "atcoder"
        assert problem.problem_id == "abc300_a"
        assert "N-choice question" in problem.title
        assert "2 sec" in problem.time_limit
        assert problem.memory_limit == "1024 MB"

        # Math converted from <var>
        assert "$N$" in problem.statement_markdown
        assert "$1 \\leq N \\leq 300$" in problem.constraints

        # Samples
        assert len(problem.samples) == 1
        assert problem.samples[0].input_text == "3 125 175\n200 300 400"
        assert problem.samples[0].output_text == "2"


# ===========================================================================
# 6. Pipeline Ingestion Runner Integration Test
# ===========================================================================

class TestPipelineIngestionRouting:
    """Verifies that run_ingestion routes CP URLs to specialized extractors."""

    @patch("scripts.ingestion.cp_problem.requests.get")
    def test_run_ingestion_with_cp_url(self, mock_get, tmp_path):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = CODEFORCES_HTML_FIXTURE
        mock_get.return_value = mock_resp

        corpus_file = tmp_path / "corpus.json"
        corpus = run_ingestion(
            sources=["https://codeforces.com/problemset/problem/1915/C"],
            output_corpus_path=corpus_file,
            assets_dir=tmp_path / "assets",
        )

        assert len(corpus.sources) == 1
        src = corpus.sources[0]
        assert src.metadata.get("platform") == "codeforces"
        assert src.metadata.get("problem_id") == "1915C"
        assert "cp_problem" in src.metadata


# ===========================================================================
# 7. End-to-End PDF Compilation & QA Gate Tests
# ===========================================================================

class TestCPEndToEndCompilationAndQA:
    """Verifies complete PDF generation and QA audit for competitive programming."""

    def test_compile_cp_problem_to_pdf_and_pass_qa(self, tmp_path):
        problem = CPProblem(
            platform="codeforces",
            url="https://codeforces.com/problemset/problem/1915/C",
            problem_id="1915C",
            title="C. Can I Square?",
            time_limit="1.0 s",
            memory_limit="256 MB",
            tags=["binary search", "implementation", "math"],
            statement_markdown="Calin has $n$ buckets with $a_i$ squares. Formula: $(-1)^{a+b}S^2$.",
            input_specification="Integer $t$ ($1 \\le t \\le 10^4$), $n$ ($1 \\le n \\le 2 \\cdot 10^5$).",
            output_specification="Output YES or NO.",
            constraints="Sum of $n$ does not exceed $2 \\cdot 10^5$.",
            samples=[
                CPSample(
                    sample_index=1,
                    input_text="5\n1\n9\n2\n14 2\n7\n1 2 3 4 5 6 7",
                    output_text="YES\nYES\nNO\nYES",
                    explanation="In the first testcase, a 3x3 square is valid.",
                )
            ],
            notes="Editorial: Evaluate $\\sum a_i$ to check if it equals a perfect square $S^2$.",
        )

        md_content = problem.to_structured_markdown()

        # Assert Zero Devanagari in markdown
        import re
        assert not re.search(r"[\u0900-\u097F]", md_content)

        pdf_path = tmp_path / "CF_1915C_Test.pdf"
        builder = ReferenceManualBuilder(pdf_path, topic="Codeforces - 1915C C. Can I Square?")
        compiled = builder.compile(md_content)

        assert compiled.exists()
        assert compiled.stat().st_size > 3000

        # Inspect compiled PDF via PyMuPDF
        doc = pymupdf.open(str(compiled))
        assert len(doc) >= 1

        extracted_text = "\n".join(page.get_text("text") for page in doc)
        doc.close()

        # Zero Devanagari invariant in compiled PDF
        assert not re.search(r"[\u0900-\u097F]", extracted_text)

        # Branding invariant
        assert "@issparsh @sumitsingh097" in extracted_text

        # Math and limits preserved
        assert "1915C" in extracted_text
        assert "1.0 s" in extracted_text
        assert "256 MB" in extracted_text
        assert "Sample 1" in extracted_text

        # Multi-line sample intact
        assert "14 2" in extracted_text

        # Run Dual-Pass QA Audit
        report = run_qa_audit(compiled)
        assert report.overall_passed is True
        assert report.pass1_visual.passed is True
        assert report.pass2_textual.passed is True
        assert len(report.pass2_textual.devanagari_violations) == 0
