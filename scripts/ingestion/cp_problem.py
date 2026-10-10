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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import lxml.html
import requests

from .unified_corpus import Chapter, CodeBlock, IngestionSource

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
            lines.append(s.input_text.strip())
            lines.append("```")
            lines.append("#### Output")
            lines.append("```")
            lines.append(s.output_text.strip())
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


def is_cp_url(url: str) -> bool:
    """Return True if url is from Codeforces, LeetCode, or AtCoder."""
    clean = url.strip()
    return bool(
        CODEFORCES_URL_PATTERN.match(clean)
        or LEETCODE_URL_PATTERN.match(clean)
        or ATCODER_URL_PATTERN.match(clean)
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
    return None


# ---------------------------------------------------------------------------
# LaTeX & HTML Sanitization Helpers
# ---------------------------------------------------------------------------

def normalize_math_delimiters(text: str) -> str:
    """Normalize various platform math markers ($$$, \\(...\\), <var>) to standard LaTeX $...$."""
    # 1. Codeforces $$$...$$$ -> $...$
    text = re.sub(r"\$\$\$([^\$]+)\$\$\$", r"$\1$", text)

    # 2. AtCoder / standard LaTeX \\(...\\) -> $...$
    text = re.sub(r"\\\((.+?)\\\)", r"$\1$", text)

    # 3. Display math \\[...\\] -> $$...$$
    text = re.sub(r"\\\[(.+?)\\\]", r"$$\1$$", text, flags=re.DOTALL)

    return text


def clean_html_formatting_to_markdown(el: lxml.html.HtmlElement) -> str:
    """Convert an HTML fragment to Markdown while preserving LaTeX math ($...$)."""
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

    return clean_text.strip()


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
                # Extract input lines preserving multi-line breaks
                in_lines_divs = in_pre.xpath(".//div[contains(@class, 'test-example-line')]")
                if in_lines_divs:
                    in_text = "\n".join(d.text_content().strip() for d in in_lines_divs)
                else:
                    # Fallback to inner HTML with br tags
                    in_text = "\n".join(line.rstrip() for line in in_pre.text_content().splitlines())
                in_text = in_text.strip()

                out_lines_divs = out_pre.xpath(".//div[contains(@class, 'test-example-line')]")
                if out_lines_divs:
                    out_text = "\n".join(d.text_content().strip() for d in out_lines_divs)
                else:
                    out_text = "\n".join(line.rstrip() for line in out_pre.text_content().splitlines())
                out_text = out_text.strip()

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
            samples_in[s_idx] = pre_el.text_content().strip() if pre_el is not None else ""
        elif "sample output" in header_lower:
            s_idx_m = re.search(r"sample output\s*(\d+)", header_lower)
            s_idx = int(s_idx_m.group(1)) if s_idx_m else len(samples_out) + 1
            pre_el = p.find(".//pre")
            out_val = pre_el.text_content().strip() if pre_el is not None else ""
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
