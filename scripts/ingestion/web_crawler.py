"""Web Documentation Crawler & DOM/Screenshot Ingestion for thenuke skill.

Features:
- Two-tier hydration: Fast Tier 1 (requests + lxml) with automatic escalation
  to Tier 2 Headless Chrome (--headless=new --dump-dom --screenshot) for SPAs.
- Noise pruning: strips navigation, menus, cookie banners, scripts, and footers.
- Structured Markdown conversion: extracts headings, tables, formatted text,
  and code blocks with language tagging.
- Full compatibility with the Unified Corpus data model.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import lxml.html
import requests

from .unified_corpus import Chapter, CodeBlock, ExtractedImage, IngestionSource

logger = logging.getLogger(__name__)

# Default Chrome locations on macOS / Linux
CHROME_CANDIDATE_PATHS = [
    os.environ.get("CHROME_BIN", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
    shutil.which("chromium-browser") or "",
    shutil.which("chrome") or "",
]


def find_chrome_binary() -> Optional[str]:
    """Locate the Google Chrome or Chromium executable on the host machine."""
    for path in CHROME_CANDIDATE_PATHS:
        if path and os.path.exists(path) and os.access(path, os.X_OK):
            return path
    return None


# ---------------------------------------------------------------------------
# HTML Cleaning & Markdown Conversion Pipeline
# ---------------------------------------------------------------------------

NOISE_TAGS = {"script", "style", "nav", "header", "footer", "aside", "form", "svg", "noscript", "iframe"}
NOISE_CLASSES_OR_IDS = [
    "sidebar", "menu", "navbar", "cookie", "banner", "footer", "header",
    "advertisement", "ad-container", "social-share", "nav-container",
]


def _remove_element_preserve_tail(el: lxml.html.HtmlElement) -> None:
    """Remove element from parent while preserving its tail text in the DOM tree."""
    parent = el.getparent()
    if parent is None:
        return
    if el.tail:
        prev = el.getprevious()
        if prev is not None:
            prev.tail = (prev.tail or "") + el.tail
        else:
            parent.text = (parent.text or "") + el.tail
    parent.remove(el)


def prune_dom_noise(root: lxml.html.HtmlElement) -> None:
    """Remove boilerplate navigational elements, scripts, styles, and ads, preserving tail text."""
    for el in list(root.iter()):
        tag = el.tag if isinstance(el.tag, str) else ""
        if tag.lower() in NOISE_TAGS:
            _remove_element_preserve_tail(el)
            continue
        
        # Check class and id attributes
        class_val = (el.get("class") or "").lower()
        id_val = (el.get("id") or "").lower()
        if any(noise in class_val or noise in id_val for noise in NOISE_CLASSES_OR_IDS):
            _remove_element_preserve_tail(el)


def extract_code_language(el: lxml.html.HtmlElement) -> str:
    """Extract language identifier from code/pre element class or attribute."""
    class_str = (el.get("class") or "").lower()
    match = re.search(r"(?:language|lang)-([a-zA-Z0-9_-]+)", class_str)
    if match:
        return match.group(1)
    
    # Check parent if this is a <code> inside a <pre>
    parent = el.getparent()
    if parent is not None:
        p_class = (parent.get("class") or "").lower()
        p_match = re.search(r"(?:language|lang)-([a-zA-Z0-9_-]+)", p_class)
        if p_match:
            return p_match.group(1)
        
    return "text"


def convert_table_to_markdown(table_el: lxml.html.HtmlElement) -> str:
    """Convert an HTML <table> into GitHub-Flavored Markdown pipe syntax."""
    rows: List[List[str]] = []
    for tr in table_el.xpath(".//tr"):
        row_cells = []
        for cell in tr.xpath("./th | ./td"):
            txt = " ".join(cell.text_content().split()).strip()
            # Escape pipes inside cell
            txt = txt.replace("|", "\\|")
            row_cells.append(txt)
        if row_cells:
            rows.append(row_cells)

    if not rows:
        return ""

    num_cols = max(len(r) for r in rows)
    padded_rows = [r + [""] * (num_cols - len(r)) for r in rows]

    md_lines = []
    # Header row
    header = padded_rows[0]
    md_lines.append("| " + " | ".join(header) + " |")
    md_lines.append("| " + " | ".join(["---"] * num_cols) + " |")
    # Data rows
    for row in padded_rows[1:]:
        md_lines.append("| " + " | ".join(row) + " |")

    return "\n" + "\n".join(md_lines) + "\n"


def html_to_markdown_and_code(
    html_content: str,
    base_url: str = "",
) -> Tuple[str, List[CodeBlock], str]:
    """Convert raw HTML to clean structured Markdown, extracted code blocks, and page title.
    
    Returns:
        (markdown_text, list_of_code_blocks, page_title)
    """
    if not html_content.strip():
        return "", [], ""

    try:
        root = lxml.html.fromstring(html_content)
    except Exception as e:
        logger.warning(f"lxml failed to parse HTML: {e}")
        return html_content, [], ""

    # Extract title
    title = ""
    title_els = root.xpath("//title")
    if title_els and title_els[0].text_content().strip():
        title = title_els[0].text_content().strip()
    elif root.xpath("//h1"):
        title = root.xpath("//h1")[0].text_content().strip()

    # Prune noise
    prune_dom_noise(root)

    # Locate main article content if possible
    article_roots = root.xpath(
        "//article | //main | //*[@role='main'] | "
        "//div[contains(@class, 'markdown-body')] | "
        "//div[contains(@class, 'content')] | "
        "//div[contains(@class, 'theme-default-content')]"
    )
    body_el = root.find(".//body")
    content_root = article_roots[0] if article_roots else (body_el if body_el is not None else root)

    code_blocks: List[CodeBlock] = []
    md_parts: List[str] = []

    def process_node(node: lxml.html.HtmlElement) -> None:
        tag = node.tag if isinstance(node.tag, str) else ""
        tag = tag.lower()

        # Headings
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tag[1])
            htext = " ".join(node.text_content().split()).strip()
            if htext:
                md_parts.append(f"\n\n{'#' * level} {htext}\n")
            return

        # Code blocks: <pre>
        if tag == "pre":
            code_el = node.find(".//code")
            target_el = code_el if code_el is not None else node
            lang = extract_code_language(target_el)
            code_text = target_el.text_content()
            # Clean trailing whitespace
            code_text = code_text.strip("\r\n")
            code_blocks.append(CodeBlock(language=lang, code=code_text))
            md_parts.append(f"\n```{lang}\n{code_text}\n```\n")
            return

        # Tables
        if tag == "table":
            table_md = convert_table_to_markdown(node)
            if table_md:
                md_parts.append(table_md)
            return

        # Blockquote
        if tag == "blockquote":
            bq_text = " ".join(node.text_content().split()).strip()
            if bq_text:
                md_parts.append(f"\n> {bq_text}\n")
            return

        # Unordered / Ordered lists
        if tag in {"ul", "ol"}:
            for i, li in enumerate(node.xpath("./li"), start=1):
                li_text = " ".join(li.text_content().split()).strip()
                prefix = f"{i}. " if tag == "ol" else "- "
                md_parts.append(f"{prefix}{li_text}\n")
            md_parts.append("\n")
            return

        # Paragraphs or divs with direct text
        if tag in {"p", "div", "section", "article"}:
            # Check if element has any descendant structured elements (even if wrapped in inline spans)
            has_blocks = bool(
                node.xpath(".//pre | .//table | .//ul | .//ol | .//h1 | .//h2 | .//h3 | .//h4 | .//h5 | .//h6 | .//blockquote")
                or any(
                    child.tag in {"p", "div", "section", "article"}
                    for child in node
                    if isinstance(child.tag, str)
                )
            )
            if has_blocks:
                for child in node:
                    if isinstance(child.tag, str):
                        process_node(child)
            else:
                p_text = " ".join(node.text_content().split()).strip()
                if p_text:
                    md_parts.append(f"\n{p_text}\n")
            return

        # Fallback recurse for container tags
        for child in node:
            if isinstance(child.tag, str):
                process_node(child)

    process_node(content_root)
    full_md = "".join(md_parts).strip()
    # Normalize excessive newlines
    full_md = re.sub(r"\n{3,}", "\n\n", full_md)

    return full_md, code_blocks, title


# ---------------------------------------------------------------------------
# Tier 1 & Tier 2 Crawling Engine
# ---------------------------------------------------------------------------

def is_spa_shell(html_content: str) -> bool:
    """Check if the downloaded HTML is an unhydrated single-page application shell."""
    cleaned = html_content.strip()
    if not cleaned:
        return True

    # Strip script and style blocks to inspect actual visible prose
    body_no_scripts = re.sub(r"<(script|style)[^>]*>[\s\S]*?</\1>", " ", cleaned, flags=re.IGNORECASE)
    visible_text = re.sub(r"<[^>]+>", " ", body_no_scripts)
    visible_text = " ".join(visible_text.split())

    # Common SPA mounting indicators with virtually empty bodies
    spa_patterns = [
        r'<div\s+id=[\'"]root[\'"]\s*>\s*</div>',
        r'<div\s+id=[\'"]app[\'"]\s*>\s*</div>',
        r'<div\s+id=[\'"]__next[\'"]\s*>\s*</div>',
        r'You need to enable JavaScript to run this app',
        r'Please enable JavaScript in your browser',
    ]
    for pattern in spa_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            # If SPA pattern is present and visible prose is small (< 250 chars)
            if len(visible_text) < 250:
                return True

    # If visible prose is virtually nonexistent (< 30 chars) and page has scripts
    if len(visible_text) < 30 and ("<script" in cleaned.lower() or len(cleaned) < 150):
        return True

    return False


def fetch_tier1_requests(url: str, timeout: int = 15) -> Tuple[int, str]:
    """Tier 1: Fast HTTP GET using requests with browser headers."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        return resp.status_code, resp.text
    except Exception as e:
        logger.warning(f"Tier 1 fetch failed for {url}: {e}")
        return 0, ""


def fetch_tier2_chrome(
    url: str,
    screenshot_path: Optional[Path] = None,
    timeout: int = 40,
) -> Tuple[int, str]:
    """Tier 2: Headless Chrome SPA DOM dump and screenshot capture.
    
    Runs Google Chrome with --headless=new --dump-dom and optionally --screenshot.
    """
    chrome_bin = find_chrome_binary()
    if not chrome_bin:
        logger.error("Google Chrome binary not found for Tier 2 crawling.")
        return 1, ""

    args = [
        chrome_bin,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1440,1080",
    ]

    if screenshot_path:
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        args.append(f"--screenshot={screenshot_path.resolve()}")

    args.extend(["--dump-dom", url])

    try:
        proc = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout
    except Exception as e:
        logger.error(f"Tier 2 Chrome execution failed: {e}")
        return 1, ""


def split_markdown_into_chapters(
    markdown_text: str,
    default_title: str = "Web Documentation",
) -> List[Chapter]:
    """Split synthesized Markdown into logical chapters based on # and ## headers."""
    lines = markdown_text.splitlines()
    sections: List[Tuple[str, List[str]]] = []
    current_title = default_title
    current_lines: List[str] = []

    header_pattern = re.compile(r"^(#{1,2})\s+(.+)$")
    in_code_block = False

    for line in lines:
        stripped_line = line.strip()
        # Toggle code fence boundary
        if stripped_line.startswith("```") or stripped_line.startswith("~~~"):
            in_code_block = not in_code_block

        match = header_pattern.match(line) if not in_code_block else None
        if match:
            if any(l.strip() for l in current_lines):
                sections.append((current_title, current_lines))
            current_title = match.group(2).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if any(l.strip() for l in current_lines):
        sections.append((current_title, current_lines))

    if not sections:
        return [
            Chapter(
                chapter_index=1,
                title=default_title,
                start_time=0.0,
                end_time=0.0,
                text=markdown_text,
            )
        ]

    chapters: List[Chapter] = []
    for idx, (sec_title, sec_lines) in enumerate(sections, start=1):
        sec_text = "\n".join(sec_lines).strip()
        chapters.append(Chapter(
            chapter_index=idx,
            title=sec_title,
            start_time=0.0,
            end_time=0.0,
            text=sec_text,
        ))

    return chapters


# ---------------------------------------------------------------------------
# High-Level Crawler Entry Points
# ---------------------------------------------------------------------------

def crawl_url(
    url: str,
    output_dir: Optional[str | Path] = None,
    capture_screenshot: bool = True,
    force_browser: bool = False,
) -> IngestionSource:
    """Crawl a web documentation URL using the 2-tier architecture.
    
    1. Tries Tier 1 (requests fast path).
    2. If empty or SPA detected (or force_browser=True), escalates to Headless Chrome.
    3. Converts DOM to clean Markdown, extracts code blocks, and saves screenshot.
    """
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid web URL: {url}")

    url_hash = hashlib.sha256(url.encode()).hexdigest()[:10]
    out_dir = Path(output_dir) if output_dir else Path(tempfile.gettempdir()) / "thenuke_web"
    out_dir.mkdir(parents=True, exist_ok=True)
    screenshot_file = (out_dir / f"web_{url_hash}.png") if capture_screenshot else None

    html_content = ""
    used_tier = "tier1_requests"

    if not force_browser:
        status_code, body = fetch_tier1_requests(url)
        if status_code == 200 and not is_spa_shell(body):
            html_content = body
            # If user wanted screenshot, run Chrome in background for screenshot only
            if capture_screenshot and screenshot_file:
                fetch_tier2_chrome(url, screenshot_path=screenshot_file, timeout=25)

    if not html_content or force_browser:
        logger.info(f"Escalating to Tier 2 Headless Chrome for {url}")
        code, dom_out = fetch_tier2_chrome(url, screenshot_path=screenshot_file)
        if code == 0 and dom_out.strip():
            html_content = dom_out
            used_tier = "tier2_chrome"
        elif not html_content:
            html_content = f"<h1>Failed to load {url}</h1><p>Crawler could not retrieve content.</p>"

    # Convert HTML to clean markdown & code blocks
    markdown_text, code_blocks, page_title = html_to_markdown_and_code(html_content, base_url=url)
    title = page_title or url

    # Split into structured chapters
    chapters = split_markdown_into_chapters(markdown_text, default_title=title)

    # IngestionSource assembly
    source = IngestionSource(
        source_type="web",
        identifier=url,
        title=title,
        metadata={
            "url": url,
            "crawler_tier": used_tier,
            "domain": urlparse(url).netloc,
            "file_type": "web_article",
        },
        chapters=chapters,
        extracted_code_blocks=code_blocks,
    )

    if capture_screenshot and screenshot_file and screenshot_file.exists():
        source.add_image(
            path=str(screenshot_file),
            caption=f"Webpage screenshot of {title}",
            ocr_text="",
        )

    return source
