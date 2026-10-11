"""Competitive Programming Problem Ingestion Engine for thenuke skill.

Features:
- Dedicated high-fidelity ingestion for:
  - Codeforces (problemset, contest, gym)
  - LeetCode (official GraphQL API + HTML fallback)
  - AtCoder (contests and tasks)
- Strict LaTeX / math preservation:
  - Converts Codeforces $$$...$$$ and AtCoder <var>...</var> to standard LaTeX $...$
  - Preserves exponents, subscripts, fractions, sums, and matrix equations
- Monospaced, structured Sample Input / Output extraction:
  - Correctly parses Codeforces test-example-line elements without text collapsing
  - Preserves exact whitespace and multi-line structures for input/output pairs
- Generates high-density, dual-register Roman Hinglish study document Markdown.
"""

from __future__ import annotations

import html
import json
import logging
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import lxml.html
import requests

from .unified_corpus import Chapter, CodeBlock, IngestionSource
from ..diagramming.reportlab_engine import normalize_and_sanitize_markdown

logger = logging.getLogger(__name__)

# Standard realistic browser headers to prevent bot-blocking
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class CPSample:
    """Represents a sample input/output test case."""
    sample_index: int
    input_text: str
    output_text: str
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_index": self.sample_index,
            "input_text": self.input_text,
            "output_text": self.output_text,
            "explanation": self.explanation,
        }


@dataclass
class CPProblem:
    """Represents a structured competitive programming problem."""
    platform: str  # "codeforces", "leetcode", "atcoder"
    url: str
    problem_id: str  # e.g. "1915C", "two-sum", "abc300_a"
    title: str
    time_limit: str = "1.0 s"
    memory_limit: str = "256 MB"
    tags: List[str] = field(default_factory=list)
    difficulty: str = ""
    statement_markdown: str = ""
    input_specification: str = ""
    output_specification: str = ""
    constraints: str = ""
    samples: List[CPSample] = field(default_factory=list)
    notes: str = ""
    hints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "url": self.url,
            "problem_id": self.problem_id,
            "title": self.title,
            "time_limit": self.time_limit,
            "memory_limit": self.memory_limit,
            "tags": self.tags,
            "difficulty": self.difficulty,
            "statement_markdown": self.statement_markdown,
            "input_specification": self.input_specification,
            "output_specification": self.output_specification,
            "constraints": self.constraints,
            "samples": [s.to_dict() for s in self.samples],
            "notes": self.notes,
            "hints": self.hints,
        }

    def to_ingestion_source(self) -> IngestionSource:
        """Convert to UnifiedCorpus IngestionSource."""
        source = IngestionSource(
            source_type="web",
            identifier=self.url,
            title=f"[{self.platform.upper()}] {self.title}",
            metadata={
                "cp_problem": self.to_dict(),
                "platform": self.platform,
                "problem_id": self.problem_id,
                "time_limit": self.time_limit,
                "memory_limit": self.memory_limit,
                "tags": self.tags,
                "difficulty": self.difficulty,
            },
        )

        # Chapter 1: Problem Statement & Math Invariants
        ch1_text = (
            f"Problem: {self.title}\n"
            f"Platform: {self.platform.upper()} (ID: {self.problem_id})\n"
            f"Time Limit: {self.time_limit} | Memory Limit: {self.memory_limit}\n"
            f"Tags: {', '.join(self.tags) if self.tags else 'None'}\n\n"
            f"Statement:\n{self.statement_markdown}\n\n"
            f"Input Specification:\n{self.input_specification}\n\n"
            f"Output Specification:\n{self.output_specification}\n"
        )
        if self.constraints:
            ch1_text += f"\nConstraints:\n{self.constraints}\n"
        source.add_chapter("Problem Specification & Mathematical Modeling", ch1_text)

        # Chapter 2: Samples & Concrete Test Cases
        ch2_parts = ["Sample Test Cases & Verifications:"]
        for s in self.samples:
            ch2_parts.append(f"\n--- Sample {s.sample_index} ---")
            ch2_parts.append(f"Input:\n{s.input_text}")
            ch2_parts.append(f"Output:\n{s.output_text}")
            if s.explanation:
                ch2_parts.append(f"Explanation:\n{s.explanation}")
            # Also register as code blocks for corpus compatibility
            source.add_code_block(s.input_text, language="text")
            source.add_code_block(s.output_text, language="text")

        if self.notes:
            ch2_parts.append(f"\nNotes & Editorial Hints:\n{self.notes}")
        source.add_chapter("Sample Executions & Edge Case Matrix", "\n".join(ch2_parts))

        return source

    def to_structured_markdown(self) -> str:
        """Generate high-density, dual-register Roman Hinglish reference manual Markdown."""
        lines: List[str] = []

        # 1. Title & Header
        lines.append(f"# {self.title}")
        lines.append(f"## {self.platform.upper()} Architecture & Engineering Reference")
        lines.append("Prepared by @issparsh @sumitsingh097")
        lines.append("")

        # 2. Metadata Bar
        tag_str = ", ".join(self.tags) if self.tags else "General"
        diff_str = f" | **Difficulty:** {self.difficulty}" if self.difficulty else ""
        lines.append(
            f"**Platform:** {self.platform.title()} | "
            f"**Problem ID:** {self.problem_id} | "
            f"**Time Limit:** {self.time_limit} | "
            f"**Memory Limit:** {self.memory_limit}{diff_str} | "
            f"**Tags:** {tag_str}"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        # 3. Problem Statement
        lines.append("### Problem Statement")
        lines.append("")
        lines.append(self.statement_markdown)
        lines.append("")

        # 4. Input Specification
        if self.input_specification:
            lines.append("### Input Specification")
            lines.append("")
            lines.append(self.input_specification)
            lines.append("")

        # 5. Output Specification
        if self.output_specification:
            lines.append("### Output Specification")
            lines.append("")
            lines.append(self.output_specification)
            lines.append("")

        # 6. Constraints
        if self.constraints:
            lines.append("### Constraints")
            lines.append("")
            lines.append(self.constraints)
            lines.append("")

        # 7. Samples (rendered using structured sample directives for ReportLab engine)
        lines.append("### Sample Tests & Verification")
        lines.append("")
        for s in self.samples:
            lines.append(f":::sample {s.sample_index}")
            lines.append("#### Input")
            lines.append("```")
            lines.append(s.input_text.strip("\r\n"))
            lines.append("```")
            lines.append("#### Output")
            lines.append("```")
            lines.append(s.output_text.strip("\r\n"))
            lines.append("```")
            if s.explanation:
                lines.append("#### Explanation")
                lines.append(s.explanation.strip())
            lines.append(":::")
            lines.append("")

        # 8. Notes
        if self.notes:
            lines.append("### Notes & Hints")
            lines.append("")
            lines.append(self.notes)
            lines.append("")

        # 9. Dual-Register Roman Hinglish Senior Architect Analysis
        lines.append("---")
        lines.append("")
        lines.append("### Senior Architect Analysis & Invariant Breakdown")
        lines.append("")
        lines.append(
            f"[MENTAL MODEL]\n"
            f"Competitive programming mein problem statement ko mathematical invariant mein map karna sabse critical step hota hai. "
            f"Is problem mein input domain aur bounds ko evaluate karke state transitions ko linear ya logarithmic time complexity mein bound karna hai."
        )
        lines.append("")
        lines.append(
            f"[ENGINEERING GOTCHA]\n"
            f"Integer overflow and large coordinate calculations: Hamesha verify karein ki accumulator variables (sum, product, area) "
            f"32-bit signed integer limit ($2^{{31}}-1 \\approx 2 \\cdot 10^9$) ko cross na karein. Large constraints mein 64-bit integer (`long long` in C++, `BigInt` in JS/Python integers) mandatory hain."
        )
        lines.append("")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Platform Detection & URL Routing
# ---------------------------------------------------------------------------

CODEFORCES_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?codeforces\.(?:com|org)/(?:contest/(\d+)/problem/([A-Za-z0-9_]+)|problemset/problem/(\d+)/([A-Za-z0-9_]+)|gym/(\d+)/problem/([A-Za-z0-9_]+))",
    re.IGNORECASE,
)

LEETCODE_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?leetcode\.(?:com|cn)/problems/([a-zA-Z0-9_\-]+)",
    re.IGNORECASE,
)

ATCODER_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?atcoder\.jp/contests/([a-zA-Z0-9_\-]+)/tasks/([a-zA-Z0-9_\-]+)",
    re.IGNORECASE,
)

CODECHEF_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?codechef\.com/(?:([a-zA-Z0-9_\-]+)/)?problems/([a-zA-Z0-9_\-]+)",
    re.IGNORECASE,
)

HACKERRANK_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?hackerrank\.com/(?:contests/[a-zA-Z0-9_\-]+/)?challenges/([a-zA-Z0-9_\-]+)(?:/problem)?",
    re.IGNORECASE,
)

GEEKSFORGEEKS_URL_PATTERN = re.compile(
    r"^https?://(?:www\.|practice\.)?geeksforgeeks\.org/problems/([a-zA-Z0-9_\-]+)",
    re.IGNORECASE,
)

INTERVIEWBIT_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?interviewbit\.com/problems/([a-zA-Z0-9_\-]+)",
    re.IGNORECASE,
)


def is_cp_url(url: str) -> bool:
    """Return True if url is from Codeforces, LeetCode, AtCoder, CodeChef, HackerRank, GeeksforGeeks, or InterviewBit."""
    clean = url.strip()
    return bool(
        CODEFORCES_URL_PATTERN.match(clean)
        or LEETCODE_URL_PATTERN.match(clean)
        or ATCODER_URL_PATTERN.match(clean)
        or CODECHEF_URL_PATTERN.match(clean)
        or HACKERRANK_URL_PATTERN.match(clean)
        or GEEKSFORGEEKS_URL_PATTERN.match(clean)
        or INTERVIEWBIT_URL_PATTERN.match(clean)
    )


def detect_cp_platform(url: str) -> Optional[str]:
    """Identify the competitive programming platform for a given URL."""
    clean = url.strip()
    if CODEFORCES_URL_PATTERN.match(clean):
        return "codeforces"
    if LEETCODE_URL_PATTERN.match(clean):
        return "leetcode"
    if ATCODER_URL_PATTERN.match(clean):
        return "atcoder"
    if CODECHEF_URL_PATTERN.match(clean):
        return "codechef"
    if HACKERRANK_URL_PATTERN.match(clean):
        return "hackerrank"
    if GEEKSFORGEEKS_URL_PATTERN.match(clean):
        return "geeksforgeeks"
    if INTERVIEWBIT_URL_PATTERN.match(clean):
        return "interviewbit"
    return None


def fetch_via_oj_api(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Fetch problem metadata, limits, and sample testcases via online-judge-tools (oj-api).
    
    Uses standard browser User-Agent to avoid bot bans.
    Returns parsed dictionary or None if unavailable.
    """
    clean_url = url.strip()
    # Normalize CodeChef URLs for oj-api: requires contest prefix like PRACTICE
    codechef_m = re.match(r"^https?://(?:www\.)?codechef\.com/problems/([a-zA-Z0-9_\-]+)", clean_url)
    if codechef_m:
        clean_url = f"https://www.codechef.com/PRACTICE/problems/{codechef_m.group(1)}"

    oj_api_bin = shutil.which("oj-api")
    if not oj_api_bin:
        return None

    try:
        cmd = [
            oj_api_bin,
            "--user-agent",
            BROWSER_HEADERS["User-Agent"],
            "get-problem",
            "--full",
            clean_url,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if res.stdout.strip():
            for line in reversed(res.stdout.splitlines()):
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        if data.get("status") == "ok":
                            return data.get("result")
                    except Exception:
                        pass
    except Exception as exc:
        logger.debug(f"oj-api invocation failed for {url}: {exc}")
    return None


# ---------------------------------------------------------------------------
# LaTeX & HTML Sanitization Helpers
# ---------------------------------------------------------------------------

def normalize_math_delimiters(text: str) -> str:
    """Normalize various platform math markers ($$$, \\(...\\), <var>) to standard LaTeX $...$."""
    # 1. Codeforces $$$...$$$ -> $...$
    text = re.sub(r"\$\$\$(.+?)\$\$\$", r"$\1$", text, flags=re.DOTALL)

    # 2. AtCoder / standard LaTeX \\(...\\) -> $...$
    text = re.sub(r"\\\((.+?)\\\)", r"$\1$", text, flags=re.DOTALL)

    # 3. Display math \\[...\\] -> $$...$$
    text = re.sub(r"\\\[(.+?)\\\]", r"$$\1$$", text, flags=re.DOTALL)

    return text


def clean_html_formatting_to_markdown(el: Any) -> str:
    """Convert an HTML fragment or string to Markdown while preserving LaTeX math ($...)."""
    if el is None:
        return ""
    if isinstance(el, str):
        if not el.strip():
            return ""
        try:
            el = lxml.html.fromstring(f"<div>{el}</div>")
        except Exception:
            return normalize_and_sanitize_markdown(normalize_math_delimiters(el)).strip()

    # Replace <var> tags with LaTeX math
    for var_el in el.xpath(".//var"):
        var_text = var_el.text_content().strip()
        if var_text:
            var_el.text = f"${var_text}$"

    # Replace <sup> and <sub> tags
    for sup_el in el.xpath(".//sup"):
        sup_text = sup_el.text_content().strip()
        sup_el.text = f"^{{{sup_text}}}"

    for sub_el in el.xpath(".//sub"):
        sub_text = sub_el.text_content().strip()
        sub_el.text = f"_{{{sub_text}}}"

    # Replace <code> tags with backticks
    for code_el in el.xpath(".//code"):
        c_text = code_el.text_content()
        code_el.text = f"`{c_text}`"

    raw_html = lxml.html.tostring(el, encoding="unicode")

    # Replace <br> or <p> with newlines
    raw_html = re.sub(r"<br\s*/?>", "\n", raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r"</p>", "\n\n", raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r"</li>", "\n", raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r"<li[^>]*>", "• ", raw_html, flags=re.IGNORECASE)

    # Strip remaining HTML tags
    clean_text = re.sub(r"<[^>]+>", "", raw_html)
    clean_text = html.unescape(clean_text)

    # Clean multiple blank lines
    clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)
    clean_text = normalize_math_delimiters(clean_text)
    clean_text = normalize_and_sanitize_markdown(clean_text)

    return clean_text.strip()


def clean_soup_to_markdown(soup_el: Any) -> str:
    """Convert a BeautifulSoup element or HTML string to Markdown while preserving LaTeX math ($...)."""
    if soup_el is None:
        return ""
    if isinstance(soup_el, str):
        if not soup_el.strip():
            return ""
        soup_el = BeautifulSoup(soup_el, "html.parser")

    for var_el in soup_el.find_all("var"):
        vt = var_el.get_text().strip()
        if vt:
            var_el.replace_with(f"${vt}$")

    for sup_el in soup_el.find_all("sup"):
        st = sup_el.get_text().strip()
        sup_el.replace_with(f"^{{{st}}}")

    for sub_el in soup_el.find_all("sub"):
        st = sub_el.get_text().strip()
        sub_el.replace_with(f"_{{{st}}}")

    for code_el in soup_el.find_all("code"):
        ct = code_el.get_text()
        code_el.replace_with(f"`{ct}`")

    for br in soup_el.find_all("br"):
        br.replace_with("\n")

    for li in soup_el.find_all("li"):
        li.insert_before("• ")
        li.append("\n")

    text = soup_el.get_text()
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = normalize_math_delimiters(text)
    text = normalize_and_sanitize_markdown(text)
    return text.strip()


# ---------------------------------------------------------------------------
# Codeforces Extractor
# ---------------------------------------------------------------------------

def extract_codeforces_problem(url: str, html_text: Optional[str] = None) -> CPProblem:
    """Extract Codeforces problem statement, limits, tags, math, and formatted samples."""
    match = CODEFORCES_URL_PATTERN.match(url.strip())
    if not match:
        raise ValueError(f"Not a valid Codeforces problem URL: {url}")

    contest_id = match.group(1) or match.group(3) or match.group(5) or ""
    problem_idx = match.group(2) or match.group(4) or match.group(6) or ""
    problem_id = f"{contest_id}{problem_idx}"

    if html_text is None:
        try:
            resp = requests.get(url, headers=BROWSER_HEADERS, timeout=8)
            resp.raise_for_status()
            html_text = resp.text
        except Exception as exc:
            logger.warning(f"Direct requests to Codeforces failed: {exc}. Attempting headless Chrome dump...")
            from .web_crawler import find_chrome_binary
            import subprocess

            chrome_bin = find_chrome_binary()
            if not chrome_bin:
                raise RuntimeError(f"Cannot fetch Codeforces URL {url}: requests failed and Chrome binary not found.")
            res = subprocess.run([chrome_bin, "--headless=new", "--dump-dom", url], capture_output=True, text=True, timeout=15)
            if res.returncode != 0 or not res.stdout.strip():
                raise RuntimeError(f"Headless Chrome failed to dump DOM for {url}")
            html_text = res.stdout

    doc = lxml.html.fromstring(html_text)
    ps_elements = doc.xpath("//div[contains(@class, 'problem-statement')]")
    if not ps_elements:
        raise ValueError(f"Could not locate '.problem-statement' in Codeforces page for {url}")

    ps = ps_elements[0]

    # 1. Title & Limits
    title_nodes = ps.xpath(".//div[@class='header']//div[@class='title']/text()")
    title = title_nodes[0].strip() if title_nodes else f"Problem {problem_id}"

    tl_nodes = ps.xpath(".//div[@class='header']//div[@class='time-limit']//text()")
    tl_raw = "".join(tl_nodes).replace("time limit per test", "").strip()
    time_limit = tl_raw if tl_raw else "1.0 s"

    ml_nodes = ps.xpath(".//div[@class='header']//div[@class='memory-limit']//text()")
    ml_raw = "".join(ml_nodes).replace("memory limit per test", "").strip()
    memory_limit = ml_raw if ml_raw else "256 MB"

    # 2. Problem Statement Body
    header_el = ps.find(".//div[@class='header']")
    if header_el is not None:
        header_el.getparent().remove(header_el)

    input_spec_el = ps.find(".//div[@class='input-specification']")
    input_spec_text = ""
    if input_spec_el is not None:
        input_spec_text = clean_html_formatting_to_markdown(input_spec_el)
        input_spec_text = re.sub(r"^Input\s*", "", input_spec_text, flags=re.IGNORECASE).strip()
        input_spec_el.getparent().remove(input_spec_el)

    output_spec_el = ps.find(".//div[@class='output-specification']")
    output_spec_text = ""
    if output_spec_el is not None:
        output_spec_text = clean_html_formatting_to_markdown(output_spec_el)
        output_spec_text = re.sub(r"^Output\s*", "", output_spec_text, flags=re.IGNORECASE).strip()
        output_spec_el.getparent().remove(output_spec_el)

    sample_tests_el = ps.find(".//div[@class='sample-tests']")
    samples: List[CPSample] = []
    if sample_tests_el is not None:
        sample_boxes = sample_tests_el.xpath(".//div[@class='sample-test']")
        for sbox in sample_boxes:
            inputs = sbox.xpath(".//div[@class='input']/pre")
            outputs = sbox.xpath(".//div[@class='output']/pre")
            for idx, (in_pre, out_pre) in enumerate(zip(inputs, outputs), start=1):
                # Extract input lines preserving multi-line breaks and indentation
                in_lines_divs = in_pre.xpath(".//div[contains(@class, 'test-example-line')]")
                if in_lines_divs:
                    in_text = "\n".join(d.text_content() for d in in_lines_divs)
                else:
                    # Fallback to inner text
                    in_text = in_pre.text_content()
                in_text = in_text.strip("\r\n")

                out_lines_divs = out_pre.xpath(".//div[contains(@class, 'test-example-line')]")
                if out_lines_divs:
                    out_text = "\n".join(d.text_content() for d in out_lines_divs)
                else:
                    out_text = out_pre.text_content()
                out_text = out_text.strip("\r\n")

                samples.append(CPSample(sample_index=idx, input_text=in_text, output_text=out_text))
        sample_tests_el.getparent().remove(sample_tests_el)

    note_el = ps.find(".//div[@class='note']")
    note_text = ""
    if note_el is not None:
        note_text = clean_html_formatting_to_markdown(note_el)
        note_text = re.sub(r"^Note\s*", "", note_text, flags=re.IGNORECASE).strip()
        note_el.getparent().remove(note_el)

    # Remaining body is the statement markdown
    statement_markdown = clean_html_formatting_to_markdown(ps)

    # 3. Tags from Codeforces sidebar
    tags: List[str] = []
    tag_spans = doc.xpath("//span[contains(@class, 'tag-box')]")
    for tspan in tag_spans:
        t_clean = tspan.text_content().strip()
        if t_clean and not t_clean.startswith("*"):
            tags.append(t_clean)

    # Fetch official API tags if local extraction was empty
    if not tags and contest_id:
        try:
            api_resp = requests.get("https://codeforces.com/api/problemset.problems", timeout=4)
            if api_resp.status_code == 200:
                p_list = api_resp.json().get("result", {}).get("problems", [])
                for p in p_list:
                    if str(p.get("contestId")) == str(contest_id) and str(p.get("index")).upper() == str(problem_idx).upper():
                        tags = p.get("tags", [])
                        break
        except Exception:
            pass

    return CPProblem(
        platform="codeforces",
        url=url,
        problem_id=problem_id,
        title=title,
        time_limit=time_limit,
        memory_limit=memory_limit,
        tags=tags,
        statement_markdown=statement_markdown,
        input_specification=input_spec_text,
        output_specification=output_spec_text,
        samples=samples,
        notes=note_text,
    )


# ---------------------------------------------------------------------------
# LeetCode Extractor (GraphQL API + Content Parser)
# ---------------------------------------------------------------------------

def extract_leetcode_problem(url: str, html_text: Optional[str] = None) -> CPProblem:
    """Extract LeetCode problem via official GraphQL query or parsed HTML."""
    match = LEETCODE_URL_PATTERN.match(url.strip())
    if not match:
        raise ValueError(f"Not a valid LeetCode problem URL: {url}")

    title_slug = match.group(1)

    # Attempt official GraphQL API
    data: Dict[str, Any] = {}
    graphql_query = """
    query questionData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId
        questionFrontendId
        title
        titleSlug
        content
        difficulty
        topicTags {
          name
          slug
        }
        hints
      }
    }
    """
    try:
        resp = requests.post(
            "https://leetcode.com/graphql",
            json={"query": graphql_query, "variables": {"titleSlug": title_slug}},
            headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {}).get("question", {}) or {}
    except Exception as exc:
        logger.warning(f"LeetCode GraphQL query failed: {exc}")

    title = data.get("title") or title_slug.replace("-", " ").title()
    frontend_id = data.get("questionFrontendId") or data.get("questionId") or title_slug
    difficulty = data.get("difficulty") or "Medium"
    tags = [t.get("name") for t in data.get("topicTags", []) if "name" in t]
    hints = data.get("hints") or []
    content_html = data.get("content") or html_text or ""

    if not content_html:
        raise RuntimeError(f"Could not retrieve problem content for LeetCode problem: {url}")

    doc = lxml.html.fromstring(f"<div>{content_html}</div>")

    # Extract examples and samples
    samples: List[CPSample] = []
    sample_blocks = doc.xpath(".//pre")
    sample_idx = 1
    for pre in sample_blocks:
        pre_text = pre.text_content().strip()
        if "Input:" in pre_text and "Output:" in pre_text:
            in_match = re.search(r"Input:\s*(.*?)(?:Output:|$)", pre_text, re.DOTALL)
            out_match = re.search(r"Output:\s*(.*?)(?:Explanation:|$)", pre_text, re.DOTALL)
            exp_match = re.search(r"Explanation:\s*(.*?)$", pre_text, re.DOTALL)

            in_val = in_match.group(1).strip() if in_match else ""
            out_val = out_match.group(1).strip() if out_match else ""
            exp_val = exp_match.group(1).strip() if exp_match else ""

            if in_val or out_val:
                samples.append(CPSample(
                    sample_index=sample_idx,
                    input_text=in_val,
                    output_text=out_val,
                    explanation=exp_val,
                ))
                sample_idx += 1
            # Remove pre block from doc so it doesn't duplicate in statement
            pre.getparent().remove(pre)

    # Extract Constraints
    constraints_text = ""
    for ul in doc.xpath(".//ul"):
        prev = ul.getprevious()
        if prev is not None and "constraint" in prev.text_content().lower():
            constraints_text = clean_html_formatting_to_markdown(ul)
            prev.getparent().remove(prev)
            ul.getparent().remove(ul)
            break

    statement_markdown = clean_html_formatting_to_markdown(doc)
    # Remove example headings from main statement text
    statement_markdown = re.sub(r"Example\s+\d+:\s*", "", statement_markdown)

    return CPProblem(
        platform="leetcode",
        url=url,
        problem_id=str(frontend_id),
        title=f"{frontend_id}. {title}",
        time_limit="1.0 s",
        memory_limit="256 MB",
        tags=tags,
        difficulty=difficulty,
        statement_markdown=statement_markdown,
        constraints=constraints_text,
        samples=samples,
        hints=hints,
    )


# ---------------------------------------------------------------------------
# AtCoder Extractor
# ---------------------------------------------------------------------------

def extract_atcoder_problem(url: str, html_text: Optional[str] = None) -> CPProblem:
    """Extract AtCoder problem statement, limits, constraints, and samples."""
    match = ATCODER_URL_PATTERN.match(url.strip())
    if not match:
        raise ValueError(f"Not a valid AtCoder problem URL: {url}")

    contest_id = match.group(1)
    task_id = match.group(2)

    if html_text is None:
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=8)
        resp.raise_for_status()
        html_text = resp.text

    doc = lxml.html.fromstring(html_text)

    # 1. Title & Limits
    h2_nodes = doc.xpath("//span[contains(@class, 'h2')]/text()")
    title = h2_nodes[0].strip() if h2_nodes else task_id.upper()

    time_limit = "2.0 s"
    memory_limit = "1024 MB"
    limit_p = doc.xpath("//p[contains(text(), 'Time Limit')]")
    if limit_p:
        l_text = limit_p[0].text_content()
        tl_m = re.search(r"Time Limit:\s*([\d\.]+\s*(?:sec|s))", l_text, re.IGNORECASE)
        ml_m = re.search(r"Memory Limit:\s*([\d\.]+\s*(?:MB|GB))", l_text, re.IGNORECASE)
        if tl_m:
            time_limit = tl_m.group(1)
        if ml_m:
            memory_limit = ml_m.group(1)

    # 2. English Section Target
    en_section = doc.xpath("//span[contains(@class, 'lang-en')]")
    target_root = en_section[0] if en_section else doc.xpath("//div[@id='task-statement']")[0]

    statement_parts: List[str] = []
    constraints_text = ""
    input_spec = ""
    output_spec = ""
    samples_in: Dict[int, str] = {}
    samples_out: Dict[int, Tuple[str, str]] = {}

    parts = target_root.xpath(".//div[contains(@class, 'part')]")
    for p in parts:
        h3_nodes = p.xpath(".//h3/text()")
        header = h3_nodes[0].strip() if h3_nodes else ""
        header_lower = header.lower()

        if "problem statement" in header_lower:
            statement_parts.append(clean_html_formatting_to_markdown(p))
        elif "constraints" in header_lower:
            constraints_text = clean_html_formatting_to_markdown(p)
            constraints_text = re.sub(r"^Constraints\s*", "", constraints_text, flags=re.IGNORECASE).strip()
        elif "input" in header_lower and "sample" not in header_lower:
            input_spec = clean_html_formatting_to_markdown(p)
            input_spec = re.sub(r"^Input\s*", "", input_spec, flags=re.IGNORECASE).strip()
        elif "output" in header_lower and "sample" not in header_lower:
            output_spec = clean_html_formatting_to_markdown(p)
            output_spec = re.sub(r"^Output\s*", "", output_spec, flags=re.IGNORECASE).strip()
        elif "sample input" in header_lower:
            s_idx_m = re.search(r"sample input\s*(\d+)", header_lower)
            s_idx = int(s_idx_m.group(1)) if s_idx_m else len(samples_in) + 1
            pre_el = p.find(".//pre")
            samples_in[s_idx] = pre_el.text_content().strip("\r\n") if pre_el is not None else ""
        elif "sample output" in header_lower:
            s_idx_m = re.search(r"sample output\s*(\d+)", header_lower)
            s_idx = int(s_idx_m.group(1)) if s_idx_m else len(samples_out) + 1
            pre_el = p.find(".//pre")
            out_val = pre_el.text_content().strip("\r\n") if pre_el is not None else ""
            # Check for explanation text following pre tag
            p_tags = p.xpath(".//p")
            exp_val = " ".join([clean_html_formatting_to_markdown(pt) for pt in p_tags]).strip()
            samples_out[s_idx] = (out_val, exp_val)

    samples: List[CPSample] = []
    for s_idx in sorted(samples_in.keys()):
        in_t = samples_in[s_idx]
        out_t, exp_t = samples_out.get(s_idx, ("", ""))
        samples.append(CPSample(sample_index=s_idx, input_text=in_t, output_text=out_t, explanation=exp_t))

    statement_markdown = "\n\n".join(statement_parts).strip()
    statement_markdown = re.sub(r"^Problem Statement\s*", "", statement_markdown, flags=re.IGNORECASE).strip()

    return CPProblem(
        platform="atcoder",
        url=url,
        problem_id=task_id,
        title=title,
        time_limit=time_limit,
        memory_limit=memory_limit,
        tags=[contest_id.upper()],
        statement_markdown=statement_markdown,
        input_specification=input_spec,
        output_specification=output_spec,
        constraints=constraints_text,
        samples=samples,
    )


# ---------------------------------------------------------------------------
# CodeChef Extractor
# ---------------------------------------------------------------------------

def extract_codechef_problem(
    url: str,
    html_text: Optional[str] = None,
    json_data: Optional[Dict[str, Any]] = None,
) -> CPProblem:
    """Extract CodeChef problem statement, limits, tags, math, and samples."""
    match = CODECHEF_URL_PATTERN.match(url.strip())
    if not match:
        raise ValueError(f"Not a valid CodeChef problem URL: {url}")

    contest_slug = match.group(1) or "PRACTICE"
    problem_code = match.group(2)

    data = json_data or {}
    if not data and html_text is None:
        api_urls = [
            f"https://www.codechef.com/api/contests/{contest_slug}/problems/{problem_code}",
            f"https://www.codechef.com/api/contests/PRACTICE/problems/{problem_code}",
        ]
        for api_url in api_urls:
            try:
                resp = requests.get(api_url, headers=BROWSER_HEADERS, timeout=8)
                if resp.status_code == 200:
                    res_json = resp.json()
                    if res_json.get("problem_name"):
                        data = res_json
                        break
            except Exception as exc:
                logger.debug(f"CodeChef API request to {api_url} failed: {exc}")

    title = data.get("problem_name") or problem_code
    max_tl = data.get("max_timelimit")
    time_limit = f"{max_tl} s" if max_tl else "1.0 s"
    memory_limit = "256 MB"
    diff = str(data.get("difficulty_rating") or "")
    tags = list(data.get("user_tags") or data.get("computed_tags") or [])
    hints = list(data.get("hints") or [])

    pc = data.get("problemComponents") or {}
    statement_raw = pc.get("statement") or data.get("body") or ""
    constraints_raw = pc.get("constraints") or ""
    input_format_raw = pc.get("inputFormat") or ""
    output_format_raw = pc.get("outputFormat") or ""
    sample_cases_data = pc.get("sampleTestCases") or []

    samples: List[CPSample] = []
    if sample_cases_data:
        for idx, sc in enumerate(sample_cases_data, start=1):
            in_t = str(sc.get("input", "")).strip()
            out_t = str(sc.get("output", "")).strip()
            exp_t = clean_soup_to_markdown(sc.get("explanation", "")).strip()
            samples.append(CPSample(sample_index=idx, input_text=in_t, output_text=out_t, explanation=exp_t))

    if (not samples or not statement_raw) and html_text:
        soup = BeautifulSoup(html_text, "html.parser")
        if not title or title == problem_code:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text().strip()
        body_div = soup.find("div", class_="problem-statement") or soup.find("div", class_="statement")
        if body_div:
            statement_raw = clean_soup_to_markdown(body_div)

    if not samples:
        oj_res = fetch_via_oj_api(url)
        if oj_res and oj_res.get("tests"):
            for idx, t in enumerate(oj_res["tests"], start=1):
                samples.append(CPSample(
                    sample_index=idx,
                    input_text=t.get("input", "").strip(),
                    output_text=t.get("output", "").strip(),
                ))

    statement_md = clean_soup_to_markdown(statement_raw)
    constraints_md = clean_soup_to_markdown(constraints_raw)
    input_md = clean_soup_to_markdown(input_format_raw)
    output_md = clean_soup_to_markdown(output_format_raw)

    return CPProblem(
        platform="codechef",
        url=url,
        problem_id=problem_code,
        title=title,
        time_limit=time_limit,
        memory_limit=memory_limit,
        tags=tags,
        difficulty=diff,
        statement_markdown=statement_md,
        input_specification=input_md,
        output_specification=output_md,
        constraints=constraints_md,
        samples=samples,
        hints=hints,
    )


# ---------------------------------------------------------------------------
# HackerRank Extractor
# ---------------------------------------------------------------------------

def extract_hackerrank_problem(
    url: str,
    html_text: Optional[str] = None,
    json_data: Optional[Dict[str, Any]] = None,
) -> CPProblem:
    """Extract HackerRank problem statement, limits, constraints, and samples."""
    match = HACKERRANK_URL_PATTERN.match(url.strip())
    if not match:
        raise ValueError(f"Not a valid HackerRank problem URL: {url}")

    slug = match.group(1)
    data = json_data or {}

    if not data and html_text is None:
        api_url = f"https://www.hackerrank.com/rest/contests/master/challenges/{slug}"
        try:
            resp = requests.get(api_url, headers=BROWSER_HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json().get("model", {})
        except Exception as exc:
            logger.debug(f"HackerRank REST API request failed: {exc}")

    title = data.get("name") or slug.replace("-", " ").title()
    difficulty = data.get("difficulty_name") or "Medium"
    track = data.get("track") or {}
    tags: List[str] = []
    if track.get("track_name"):
        tags.append(track["track_name"])
    if track.get("name"):
        tags.append(track["name"])

    statement_md = data.get("problem_statement") or ""
    input_spec = data.get("input_format") or ""
    constraints = data.get("constraints") or ""
    output_spec = data.get("output_format") or ""
    body_html = data.get("body_html") or html_text or ""

    samples: List[CPSample] = []
    if body_html:
        soup = BeautifulSoup(body_html, "html.parser")
        pres = soup.find_all("pre")
        if len(pres) >= 2:
            idx = 1
            for i in range(0, len(pres) - 1, 2):
                in_t = pres[i].get_text().strip()
                out_t = pres[i+1].get_text().strip()
                samples.append(CPSample(sample_index=idx, input_text=in_t, output_text=out_t))
                idx += 1

    if not samples:
        oj_res = fetch_via_oj_api(url)
        if oj_res and oj_res.get("tests"):
            for idx, t in enumerate(oj_res["tests"], start=1):
                samples.append(CPSample(
                    sample_index=idx,
                    input_text=t.get("input", "").strip(),
                    output_text=t.get("output", "").strip(),
                ))

    statement_md = normalize_and_sanitize_markdown(normalize_math_delimiters(statement_md))
    constraints = normalize_and_sanitize_markdown(normalize_math_delimiters(constraints))
    input_spec = normalize_and_sanitize_markdown(normalize_math_delimiters(input_spec))
    output_spec = normalize_and_sanitize_markdown(normalize_math_delimiters(output_spec))

    return CPProblem(
        platform="hackerrank",
        url=url,
        problem_id=slug,
        title=title,
        time_limit="2.0 s",
        memory_limit="512 MB",
        tags=tags,
        difficulty=difficulty,
        statement_markdown=statement_md,
        input_specification=input_spec,
        output_specification=output_spec,
        constraints=constraints,
        samples=samples,
    )


# ---------------------------------------------------------------------------
# GeeksforGeeks Extractor
# ---------------------------------------------------------------------------

def extract_geeksforgeeks_problem(url: str, html_text: Optional[str] = None) -> CPProblem:
    """Extract GeeksforGeeks problem statement, constraints, company/topic tags, and samples."""
    match = GEEKSFORGEEKS_URL_PATTERN.match(url.strip())
    if not match:
        raise ValueError(f"Not a valid GeeksforGeeks problem URL: {url}")

    slug = match.group(1)

    if html_text is None:
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=8)
        resp.raise_for_status()
        html_text = resp.text

    title = slug.replace("-", " ").title()
    difficulty = "Medium"
    tags: List[str] = []
    question_html = ""
    constraints = ""

    soup = BeautifulSoup(html_text, "html.parser")
    next_script = soup.find("script", id="__NEXT_DATA__")
    if next_script and next_script.string:
        try:
            ndata = json.loads(next_script.string)
            pdata = ndata.get("props", {}).get("pageProps", {}).get("initialState", {}).get("problemData", {}).get("allData", {}).get("probData", {})
            if pdata:
                title = pdata.get("problem_name") or title
                difficulty = pdata.get("difficulty") or difficulty
                tags_obj = pdata.get("tags") or {}
                topic_tags = tags_obj.get("topic_tags", []) if isinstance(tags_obj, dict) else []
                comp_tags = tags_obj.get("company_tags", []) if isinstance(tags_obj, dict) else []
                tags = list(topic_tags) + list(comp_tags)
                question_html = pdata.get("problem_question") or ""
                constraints = pdata.get("constraints_display") or ""
        except Exception as exc:
            logger.debug(f"Error parsing GFG __NEXT_DATA__: {exc}")

    if not question_html:
        q_div = soup.find("div", class_="problems_problem_content__Xm_eO") or soup.find("div", class_="problem-statement")
        if q_div:
            question_html = str(q_div)

    samples: List[CPSample] = []
    if question_html:
        q_soup = BeautifulSoup(question_html, "html.parser")
        pres = q_soup.find_all("pre")
        for idx, pre in enumerate(pres, start=1):
            txt = pre.get_text()
            if "Input:" in txt or "Output:" in txt:
                in_m = re.search(r"Input:\s*(.*?)(?:Output:|$)", txt, re.DOTALL)
                out_m = re.search(r"Output:\s*(.*?)(?:Explanation:|$)", txt, re.DOTALL)
                exp_m = re.search(r"Explanation:\s*(.*?)$", txt, re.DOTALL)
                in_v = in_m.group(1).strip() if in_m else ""
                out_v = out_m.group(1).strip() if out_m else ""
                exp_v = exp_m.group(1).strip() if exp_m else ""
                samples.append(CPSample(sample_index=idx, input_text=in_v, output_text=out_v, explanation=exp_v))
                pre.decompose()

        statement_md = clean_soup_to_markdown(q_soup)
    else:
        statement_md = clean_soup_to_markdown(soup)

    return CPProblem(
        platform="geeksforgeeks",
        url=url,
        problem_id=slug,
        title=title,
        time_limit="1.0 s",
        memory_limit="256 MB",
        tags=tags,
        difficulty=difficulty,
        statement_markdown=statement_md,
        constraints=clean_soup_to_markdown(constraints),
        samples=samples,
    )


# ---------------------------------------------------------------------------
# InterviewBit Extractor
# ---------------------------------------------------------------------------

def extract_interviewbit_problem(url: str, html_text: Optional[str] = None) -> CPProblem:
    """Extract InterviewBit problem statement, constraints, companies, and samples."""
    match = INTERVIEWBIT_URL_PATTERN.match(url.strip())
    if not match:
        raise ValueError(f"Not a valid InterviewBit problem URL: {url}")

    slug = match.group(1)

    if html_text is None:
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=8)
        resp.raise_for_status()
        html_text = resp.text

    title = slug.replace("-", " ").title()
    difficulty = "Medium"
    tags: List[str] = []
    statement_md = ""
    constraints_md = ""
    input_md = ""
    output_md = ""
    hints: List[str] = []
    samples: List[CPSample] = []

    m = re.search(r"window\.__INTERVIEWBIT__\.problemsData\s*=\s*(\{.+?\});", html_text, re.DOTALL)
    if m:
        try:
            pdata = json.loads(m.group(1))
            meta = pdata.get("meta") or {}
            title = meta.get("statement") or title
            difficulty = meta.get("difficulty_level") or difficulty
            tags = list(meta.get("companies") or [])
            if pdata.get("topic", {}).get("slug"):
                tags.append(pdata["topic"]["slug"])
            hints = list(pdata.get("hints") or [])

            raw_md = meta.get("markdown_content") or ""
            if raw_md:
                soup = BeautifulSoup(raw_md, "html.parser")
                desc_div = soup.find("div", id="problem_description_markdown_content_value")
                const_div = soup.find("div", id="problem_constraints_markdown_content_value")
                in_div = soup.find("div", id="input_format_markdown_content_value")
                out_div = soup.find("div", id="output_format_markdown_content_value")
                ex_in_div = soup.find("div", id="example_input_markdown_content_value")
                ex_out_div = soup.find("div", id="example_output_markdown_content_value")
                ex_exp_div = soup.find("div", id="example_explanation_markdown_content_value")

                if desc_div:
                    statement_md = clean_soup_to_markdown(desc_div)
                if const_div:
                    constraints_md = clean_soup_to_markdown(const_div)
                if in_div:
                    input_md = clean_soup_to_markdown(in_div)
                if out_div:
                    output_md = clean_soup_to_markdown(out_div)

                in_pres = [p.get_text().strip() for p in ex_in_div.find_all("pre")] if ex_in_div else []
                out_pres = [p.get_text().strip() for p in ex_out_div.find_all("pre")] if ex_out_div else []
                exp_pres = [p.get_text().strip() for p in ex_exp_div.find_all("pre")] if ex_exp_div else []

                for idx in range(max(len(in_pres), len(out_pres))):
                    inp = in_pres[idx] if idx < len(in_pres) else ""
                    outp = out_pres[idx] if idx < len(out_pres) else ""
                    exp = exp_pres[idx] if idx < len(exp_pres) else ""
                    samples.append(CPSample(sample_index=idx + 1, input_text=inp, output_text=outp, explanation=exp))
        except Exception as exc:
            logger.debug(f"Error parsing InterviewBit problemsData JSON: {exc}")

    if not statement_md:
        soup = BeautifulSoup(html_text, "html.parser")
        statement_md = clean_soup_to_markdown(soup)

    return CPProblem(
        platform="interviewbit",
        url=url,
        problem_id=slug,
        title=title,
        time_limit="1.0 s",
        memory_limit="256 MB",
        tags=tags,
        difficulty=difficulty,
        statement_markdown=statement_md,
        input_specification=input_md,
        output_specification=output_md,
        constraints=constraints_md,
        samples=samples,
        hints=hints,
    )


# ---------------------------------------------------------------------------
# Unified Extraction Dispatcher
# ---------------------------------------------------------------------------

def extract_cp_problem(url: str, html_text: Optional[str] = None) -> CPProblem:
    """Dispatcher to parse any supported competitive programming problem."""
    platform = detect_cp_platform(url)
    if platform == "codeforces":
        return extract_codeforces_problem(url, html_text=html_text)
    elif platform == "leetcode":
        return extract_leetcode_problem(url, html_text=html_text)
    elif platform == "atcoder":
        return extract_atcoder_problem(url, html_text=html_text)
    elif platform == "codechef":
        return extract_codechef_problem(url, html_text=html_text)
    elif platform == "hackerrank":
        return extract_hackerrank_problem(url, html_text=html_text)
    elif platform == "geeksforgeeks":
        return extract_geeksforgeeks_problem(url, html_text=html_text)
    elif platform == "interviewbit":
        return extract_interviewbit_problem(url, html_text=html_text)
    else:
        raise ValueError(f"Unsupported competitive programming platform for URL: {url}")


def ingest_cp_problem(url: str, output_dir: Optional[Path] = None, html_text: Optional[str] = None) -> IngestionSource:
    """Top-level ingestion pipeline function that produces an IngestionSource."""
    problem = extract_cp_problem(url, html_text=html_text)
    source = problem.to_ingestion_source()

    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        meta_file = out_path / f"cp_{problem.platform}_{problem.problem_id}.json"
        meta_file.write_text(json.dumps(problem.to_dict(), indent=2), encoding="utf-8")
        logger.info(f"Saved CP problem metadata to {meta_file}")

    return source
