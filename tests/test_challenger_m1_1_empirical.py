"""Adversarial Empirical Stress & Bug Reproduction Suite for Milestone 1 Ingestion.

Authored by Milestone 1 Challenger 1 (teamwork_preview_challenger_m1_1).
Empirically tests and stress-tests:
1. VTT Rolling-Window Deduplication on progressive subtitle streams and programming syntax.
2. DOM Extraction, noise pruning, tail text preservation, and markdown chapter splitting.
3. Malformed URLs, port handling, and malformed/corrupted local files.
4. Fuzz generators and oracles for subtitle and HTML parsing.
"""

from __future__ import annotations

import json
import os
import random
import string
import tempfile
from pathlib import Path
from typing import Any, Dict, List
import lxml.html
import pytest

from scripts.ingestion import (
    Chapter,
    CodeBlock,
    IngestionSource,
    UnifiedCorpus,
    align_cues_to_chapters,
    clean_vtt_content,
    crawl_url,
    deduplicate_vtt_cues,
    extract_local_file,
    extract_pdf,
    extract_pptx,
    html_to_markdown_and_code,
    is_playlist_url,
    is_youtube_url,
    parse_vtt_cues,
    run_ingestion,
)
from scripts.ingestion.file_extract import detect_code_blocks
from scripts.ingestion.web_crawler import prune_dom_noise, split_markdown_into_chapters
from scripts.ingestion.yt_ingest import extract_video_id, strip_vtt_markup


# ===========================================================================
# 1. VTT Rolling-Window Deduplication Empirical Challenges
# ===========================================================================

class TestVTTDeduplicationAdversarial:
    """Empirical challenges against VTT subtitle parsing and deduplication."""

    def test_progressive_word_by_word_subtitles_causes_multiplication(self):
        """CHALLENGE: Progressive subtitle updates (YouTube live captions)

        When words arrive incrementally across consecutive cues:
        Cue 1: "the quick brown"
        Cue 2: "the quick brown fox"
        Cue 3: "the quick brown fox jumps"

        Expected: The output should collapse into "the quick brown fox jumps" (5 words).
        Observed Failure: deduplicate_vtt_cues appends each line, producing:
        "the quick brown the quick brown fox the quick brown fox jumps" (12 words).
        """
        cues = [
            {"start": 1.0, "end": 2.0, "lines": ["the quick brown"], "text": "the quick brown"},
            {"start": 2.0, "end": 3.0, "lines": ["the quick brown fox"], "text": "the quick brown fox"},
            {"start": 3.0, "end": 4.0, "lines": ["the quick brown fox jumps"], "text": "the quick brown fox jumps"},
        ]

        deduped = deduplicate_vtt_cues(cues)
        merged_text = " ".join(c["text"] for c in deduped)

        # Bug check: "the quick brown" must not appear 3 times
        occurrences = merged_text.count("the quick brown")
        assert occurrences == 1, (
            f"VTT progressive deduplication failed! 'the quick brown' appeared {occurrences} times in: '{merged_text}'"
        )

    def test_strip_vtt_markup_mutilates_programming_comparisons_and_generics(self):
        """CHALLENGE: Over-aggressive regex in strip_vtt_markup mutates programming syntax.

        In engineering lectures, transcripts contain code comparisons and generic types:
        - "if x < 10 and y > 20"
        - "Promise<Response>"
        - "Array<string>"

        strip_vtt_markup regex r"<[^>]+>" treats `< 10 and y >` and `<Response>` as HTML tags
        and strips them out entirely.
        """
        code_sub = "We check if x < 10 and y > 20 in the loop."
        cleaned = strip_vtt_markup(code_sub)
        assert "< 10 and y >" in cleaned or ("< 10" in cleaned and "> 20" in cleaned), (
            f"strip_vtt_markup mutilated programming comparison: '{cleaned}'"
        )

        generics_sub = "The function returns Promise<Response> or Array<string>."
        cleaned_gen = strip_vtt_markup(generics_sub)
        assert "Promise<Response>" in cleaned_gen or "<Response>" in cleaned_gen, (
            f"strip_vtt_markup mutilated generic type: '{cleaned_gen}'"
        )

    def test_substring_match_in_deduplication_causes_false_replacement(self):
        """CHALLENGE: 'last_line.lower() in normalized_line' uses substring rather than prefix.

        If Cue 1 emitted a short word like 'an', and Cue 2 says 'understanding the event loop',
        'an' in 'understanding...' is True, causing Cue 2 to falsely trigger the replacement branch!
        """
        cues = [
            {"start": 1.0, "end": 2.0, "lines": ["an"], "text": "an"},
            {"start": 2.0, "end": 3.0, "lines": ["understanding the event loop"], "text": "understanding the event loop"},
        ]
        deduped = deduplicate_vtt_cues(cues)
        # Both distinct utterances must be preserved
        all_text = " ".join(c["text"] for c in deduped)
        assert "an" in all_text.split()
        assert "understanding" in all_text

    def test_cue_identifier_without_blank_line_bleeds_into_cue_text(self):
        """CHALLENGE: VTT files where cue numbers have no leading blank line.

        Standard WebVTT or SRT often has cues without double blank lines:
        00:00:01.000 --> 00:00:02.000
        First line
        2
        00:00:02.000 --> 00:00:03.000
        Second line

        parse_vtt_cues appends '2' as text to cue 1 instead of discarding it as cue id.
        """
        raw_vtt = """WEBVTT

00:00:01.000 --> 00:00:02.000
First line
2
00:00:02.000 --> 00:00:03.000
Second line
"""
        cues = parse_vtt_cues(raw_vtt)
        assert len(cues) == 2
        assert cues[0]["text"] == "First line", f"Cue id '2' bled into cue text: {cues[0]['text']}"


# ===========================================================================
# 2. Web Crawler & DOM Extraction Adversarial Challenges
# ===========================================================================

class TestDOMExtractionAdversarial:
    """Empirical challenges against HTML cleaning, DOM noise pruning, and Markdown splitting."""

    def test_code_comments_cleave_markdown_code_blocks(self):
        r"""CHALLENGE: split_markdown_into_chapters splits code blocks on '#' comments.

        In documentation with Python, Shell, Ruby, or Dockerfile code blocks:
        ```python
        # Step 1: Initialize database
        db = connect()
        ## Step 2: Run migrations
        migrate(db)
        ```

        split_markdown_into_chapters checks header_pattern r"^(#{1,2})\s+(.+)$" on ALL lines,
        even inside code fences. It splits the code block across 3 chapters, breaking code fences!
        """
        markdown_doc = """# Database Migration Guide

Here is the setup script:

```python
# Step 1: Initialize database
db = connect()
## Step 2: Run migrations
migrate(db)
```

Ensure this script is executed with root privileges.
"""
        chapters = split_markdown_into_chapters(markdown_doc)

        # There should only be 1 chapter ("Database Migration Guide")
        assert len(chapters) == 1, (
            f"Code block comments cleaved doc into {len(chapters)} chapters! "
            f"Chapter titles: {[c.title for c in chapters]}"
        )
        assert "```python" in chapters[0].text
        assert "```" in chapters[0].text

    def test_prune_dom_noise_silently_destroys_tail_text(self):
        """CHALLENGE: lxml parent.remove(el) destroys el.tail text.

        In HTML:
        <p>Before noise <span class="cookie-banner">Banner</span> after noise critical text.</p>

        When prune_dom_noise removes the <span class="cookie-banner">,
        in lxml, the child's .tail (' after noise critical text.') is destroyed!
        """
        html = '<div><p>Before noise <span class="cookie-banner">Banner</span> after noise critical text.</p></div>'
        root = lxml.html.fromstring(html)
        prune_dom_noise(root)
        extracted_text = " ".join(root.text_content().split())

        assert "after noise critical text" in extracted_text, (
            f"prune_dom_noise deleted tail text! Extracted only: '{extracted_text}'"
        )

    def test_code_blocks_inside_inline_tags_are_not_ignored(self):
        """CHALLENGE: <pre> inside inline tags (e.g. <span> or <div> without block tag siblings).

        If a document wraps <pre><code> inside <div><span><pre>...,
        web_crawler's process_node check `has_blocks` fails to find block tags if span is direct child,
        and extracts it as plain text without CodeBlock or language formatting.
        """
        html = """
        <div class="content">
            <span class="code-wrapper">
                <pre><code class="language-javascript">const answer = 42;</code></pre>
            </span>
        </div>
        """
        md, code_blocks, _ = html_to_markdown_and_code(html)
        assert len(code_blocks) >= 1, "Failed to extract code block nested inside inline container"
        assert "```javascript" in md


# ===========================================================================
# 3. Malformed URLs and File Extraction Challenges
# ===========================================================================

class TestMalformedURLsAndFilesAdversarial:
    """Empirical challenges against URL validators and file extractors."""

    def test_is_youtube_url_with_explicit_port(self):
        """CHALLENGE: is_youtube_url fails on valid YouTube URLs with explicit port.

        Standard URLs like 'https://youtube.com:443/watch?v=dQw4w9WgXcQ' are valid URLs,
        but urlparse().netloc includes ':443', failing the exact domain set check.
        """
        url_with_port = "https://youtube.com:443/watch?v=dQw4w9WgXcQ"
        assert is_youtube_url(url_with_port), (
            f"is_youtube_url rejected valid URL with explicit port :443: '{url_with_port}'"
        )
        vid_id = extract_video_id(url_with_port)
        assert vid_id == "dQw4w9WgXcQ"

    def test_extract_local_file_on_corrupted_pdf_raises_or_isolates(self, tmp_path):
        """CHALLENGE: extract_local_file on corrupted PDF without catching error directly."""
        corrupt_pdf = tmp_path / "broken.pdf"
        corrupt_pdf.write_bytes(b"INVALID_PDF_HEADER_DATA")

        # extract_local_file directly raises FileDataError
        with pytest.raises(Exception):
            extract_local_file(corrupt_pdf)

    def test_extract_local_file_on_zero_byte_pptx_raises_or_isolates(self, tmp_path):
        """CHALLENGE: extract_local_file on zero-byte pptx raises PackageNotFoundError."""
        zero_pptx = tmp_path / "empty.pptx"
        zero_pptx.write_bytes(b"")

        with pytest.raises(Exception):
            extract_local_file(zero_pptx)


# ===========================================================================
# 4. Stress Generator & Oracle Harnesses
# ===========================================================================

class TestGeneratorOraclesStress:
    """Randomized fuzz generators and invariance oracles."""

    def test_vtt_randomized_rolling_window_oracle(self):
        """ORACLE: Given N unique lines rolling through 3-line windows,

        the output MUST contain every line exactly once in order.
        """
        # Generate 20 distinct synthetic sentences
        sentences = [f"Unique sentence {i:02d} for topic." for i in range(20)]
        cues = []
        for i in range(len(sentences) - 2):
            window = sentences[i : i + 3]
            cues.append({
                "start": float(i * 2),
                "end": float((i + 1) * 2),
                "lines": window,
                "text": " ".join(window),
            })

        deduped = deduplicate_vtt_cues(cues)
        emitted_full = " ".join(c["text"] for c in deduped)

        # Oracle assertion: Each sentence 0..19 must appear at least once and at most once
        for s in sentences:
            count = emitted_full.count(s)
            assert count == 1, f"Sentence '{s}' appeared {count} times (expected exactly 1)"

    def test_html_fuzzer_resilience(self):
        """ORACLE: html_to_markdown_and_code must never crash on random mutated HTML."""
        fuzz_samples = [
            "<html><body>" + "<p>Unclosed paragraph" * 10,
            "<table><tr><td>" + "<tr><td>Cell" * 5 + "</table>",
            "<div><script>alert(1)</script><p>Text</p><style>body{}</style></div>",
            "<pre><code>" + "\x00\x01\x02\x03" + "</code></pre>",
            "<a href='" + "x" * 1000 + "'>Link</a>",
            "<!-- unclosed comment <p>Hello</p>",
        ]

        for sample in fuzz_samples:
            try:
                md, cbs, title = html_to_markdown_and_code(sample)
                assert isinstance(md, str)
                assert isinstance(cbs, list)
            except Exception as exc:
                pytest.fail(f"html_to_markdown_and_code crashed on fuzzed HTML: {exc}")
