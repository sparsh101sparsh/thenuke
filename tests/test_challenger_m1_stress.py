"""Empirical Adversarial Stress Test Suite for Milestone 1 Ingestion Engine.

Written by Milestone 1 Challenger 2 (teamwork_preview_challenger).
Tests unified runner `run_ingestion()`, corrupted inputs, schema resilience,
high-volume batch processing, adversarial HTML, and VTT edge cases.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pymupdf
import pytest
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt

from scripts.ingestion import (
    Chapter,
    CodeBlock,
    ExtractedImage,
    IngestionSource,
    UnifiedCorpus,
    align_cues_to_chapters,
    clean_vtt_content,
    crawl_url,
    deduplicate_vtt_cues,
    extract_directory,
    extract_image,
    extract_local_file,
    extract_media,
    extract_pdf,
    extract_pptx,
    extract_text_file,
    html_to_markdown_and_code,
    is_playlist_url,
    is_youtube_url,
    parse_vtt_cues,
    run_ingestion,
)
from scripts.ingestion.file_extract import detect_code_blocks
from scripts.ingestion.web_crawler import convert_table_to_markdown, is_spa_shell, split_markdown_into_chapters
from scripts.ingestion.yt_ingest import extract_video_id, parse_timestamp_seconds, strip_vtt_markup


# ===========================================================================
# Schema Validator Helper Oracle
# ===========================================================================

def assert_valid_corpus_contract(data: dict):
    """Oracle function validating strict compliance with PROJECT.md § 4.1."""
    assert isinstance(data, dict), "Corpus must be a JSON object"
    assert "corpus_id" in data, "Missing required key: corpus_id"
    assert isinstance(data["corpus_id"], str) and data["corpus_id"], "corpus_id must be non-empty string"
    assert "timestamp" in data, "Missing required key: timestamp"
    # Validate ISO8601 format
    try:
        datetime.fromisoformat(data["timestamp"])
    except Exception as e:
        pytest.fail(f"timestamp '{data['timestamp']}' is not valid ISO8601: {e}")

    assert "sources" in data, "Missing required key: sources"
    assert isinstance(data["sources"], list), "sources must be a list"

    assert "aggregated_topics" in data, "Missing required key: aggregated_topics"
    assert isinstance(data["aggregated_topics"], list), "aggregated_topics must be a list"
    assert all(isinstance(t, str) for t in data["aggregated_topics"]), "All topics must be strings"

    for idx, src in enumerate(data["sources"]):
        prefix = f"Source [{idx}]"
        assert "source_type" in src, f"{prefix} missing source_type"
        assert src["source_type"] in {"youtube", "web", "local_file"}, f"{prefix} invalid source_type: {src['source_type']}"
        assert "identifier" in src, f"{prefix} missing identifier"
        assert isinstance(src["identifier"], str), f"{prefix} identifier must be string"
        assert "title" in src, f"{prefix} missing title"
        assert isinstance(src["title"], str), f"{prefix} title must be string"
        assert "metadata" in src, f"{prefix} missing metadata"
        assert isinstance(src["metadata"], dict), f"{prefix} metadata must be dict"

        # Chapters
        assert "chapters" in src, f"{prefix} missing chapters"
        assert isinstance(src["chapters"], list), f"{prefix} chapters must be list"
        for cidx, chap in enumerate(src["chapters"]):
            c_prefix = f"{prefix} Chapter [{cidx}]"
            assert "chapter_index" in chap, f"{c_prefix} missing chapter_index"
            assert isinstance(chap["chapter_index"], int), f"{c_prefix} chapter_index must be int"
            assert "title" in chap, f"{c_prefix} missing title"
            assert isinstance(chap["title"], str), f"{c_prefix} title must be str"
            assert "start_time" in chap, f"{c_prefix} missing start_time"
            assert isinstance(chap["start_time"], (int, float)), f"{c_prefix} start_time must be float"
            assert "end_time" in chap, f"{c_prefix} missing end_time"
            assert isinstance(chap["end_time"], (int, float)), f"{c_prefix} end_time must be float"
            assert "text" in chap, f"{c_prefix} missing text"
            assert isinstance(chap["text"], str), f"{c_prefix} text must be str"

        # Extracted Code Blocks
        assert "extracted_code_blocks" in src, f"{prefix} missing extracted_code_blocks"
        assert isinstance(src["extracted_code_blocks"], list), f"{prefix} extracted_code_blocks must be list"
        for cb_idx, cb in enumerate(src["extracted_code_blocks"]):
            cb_prefix = f"{prefix} CodeBlock [{cb_idx}]"
            assert "language" in cb, f"{cb_prefix} missing language"
            assert isinstance(cb["language"], str), f"{cb_prefix} language must be str"
            assert "code" in cb, f"{cb_prefix} missing code"
            assert isinstance(cb["code"], str), f"{cb_prefix} code must be str"

        # Extracted Images
        assert "extracted_images" in src, f"{prefix} missing extracted_images"
        assert isinstance(src["extracted_images"], list), f"{prefix} extracted_images must be list"
        for img_idx, img in enumerate(src["extracted_images"]):
            img_prefix = f"{prefix} ExtractedImage [{img_idx}]"
            assert "path" in img, f"{img_prefix} missing path"
            assert isinstance(img["path"], str), f"{img_prefix} path must be str"
            assert "caption" in img, f"{img_prefix} missing caption"
            assert isinstance(img["caption"], str), f"{img_prefix} caption must be str"
            assert "ocr_text" in img, f"{img_prefix} missing ocr_text"
            assert isinstance(img["ocr_text"], str), f"{img_prefix} ocr_text must be str"


# ===========================================================================
# 1. Corrupted, Truncated & Zero-Byte Input Stress Tests
# ===========================================================================

class TestCorruptedAndZeroByteStress:
    """Stress tests extractors and runner with adversarial binary states."""

    def test_zero_byte_pdf_handling(self, tmp_path):
        """0-byte PDF should be rejected by extract_pdf, but isolated gracefully in extract_directory & run_ingestion."""
        zero_pdf = tmp_path / "empty.pdf"
        zero_pdf.write_bytes(b"")

        # Calling extract_pdf directly raises FileDataError
        with pytest.raises(Exception):
            extract_pdf(zero_pdf, output_dir=tmp_path)

        # But extract_directory isolates individual file failures
        dir_sources = extract_directory(tmp_path, output_dir=tmp_path)
        assert len(dir_sources) == 0

        # And run_ingestion logs error and produces valid corpus without crashing
        corpus_path = tmp_path / "corpus.json"
        corpus = run_ingestion([str(zero_pdf)], output_corpus_path=corpus_path, assets_dir=tmp_path)
        assert isinstance(corpus, UnifiedCorpus)
        assert len(corpus.sources) == 0
        assert_valid_corpus_contract(json.loads(corpus_path.read_text()))

    def test_corrupted_garbage_pdf_handling(self, tmp_path):
        """Random binary garbage disguised as .pdf."""
        bad_pdf = tmp_path / "corrupted.pdf"
        bad_pdf.write_bytes(b"%PDF-1.4\n\x00\xff\xfe\x12\x34\x56" * 50)

        with pytest.raises(Exception):
            extract_pdf(bad_pdf, output_dir=tmp_path)

        # run_ingestion survives
        corpus = run_ingestion([str(bad_pdf)], output_corpus_path=tmp_path / "corpus.json", assets_dir=tmp_path)
        assert len(corpus.sources) == 0

    def test_zero_byte_pptx_handling(self, tmp_path):
        """0-byte PPTX should be caught and isolated."""
        zero_pptx = tmp_path / "empty.pptx"
        zero_pptx.write_bytes(b"")

        with pytest.raises(Exception):
            extract_pptx(zero_pptx, output_dir=tmp_path)

        corpus = run_ingestion([str(zero_pptx)], output_corpus_path=tmp_path / "corpus.json", assets_dir=tmp_path)
        assert len(corpus.sources) == 0

    def test_corrupted_zip_pptx_handling(self, tmp_path):
        """Corrupted ZIP archive as .pptx."""
        corrupt_pptx = tmp_path / "bad.pptx"
        corrupt_pptx.write_bytes(b"PK\x03\x04\x00\x00corrupted_non_zip_data_stream")

        with pytest.raises(Exception):
            extract_pptx(corrupt_pptx, output_dir=tmp_path)

        corpus = run_ingestion([str(corrupt_pptx)], output_corpus_path=tmp_path / "corpus.json", assets_dir=tmp_path)
        assert len(corpus.sources) == 0

    def test_zero_byte_image_handling(self, tmp_path):
        """0-byte image file should not crash extract_image."""
        zero_img = tmp_path / "empty.png"
        zero_img.write_bytes(b"")

        # extract_image handles broken images gracefully (format="IMAGE", width=0, height=0)
        source = extract_image(zero_img, output_dir=tmp_path)
        assert source.source_type == "local_file"
        assert source.metadata["file_type"] == "image"
        assert source.metadata["width"] == 0
        assert source.metadata["height"] == 0
        assert len(source.chapters) == 1

    def test_corrupted_truncated_image_handling(self, tmp_path):
        """Truncated image with partial PNG header."""
        bad_img = tmp_path / "bad.png"
        bad_img.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01")

        source = extract_image(bad_img, output_dir=tmp_path)
        assert source.source_type == "local_file"
        assert source.metadata["width"] == 0

    def test_zero_byte_text_and_markdown(self, tmp_path):
        """0-byte text and markdown files extract successfully as empty chapters."""
        zero_md = tmp_path / "empty.md"
        zero_md.write_text("")

        source = extract_text_file(zero_md)
        assert source.title == "empty"
        assert len(source.chapters) == 1
        assert source.chapters[0].text == ""
        assert len(source.extracted_code_blocks) == 0

    def test_directory_with_mixed_valid_and_corrupted_files(self, tmp_path):
        """Directory extraction must succeed on valid files even if corrupt siblings exist."""
        work = tmp_path / "mixed_dir"
        work.mkdir()

        # 1. Valid markdown file
        (work / "valid1.md").write_text("# Topic 1\nClean documentation content here.")
        # 2. Corrupted PDF
        (work / "corrupt.pdf").write_bytes(b"not a valid pdf")
        # 3. 0-byte PPTX
        (work / "zero.pptx").write_bytes(b"")
        # 4. Valid plain text
        (work / "valid2.txt").write_text("Plain text documentation notes.")
        # 5. Unsupported hidden file
        (work / ".ignored.tmp").write_text("hidden")

        sources = extract_directory(work, output_dir=tmp_path)
        # Should have successfully extracted valid1.md and valid2.txt, skipping the broken ones
        assert len(sources) == 2
        titles = {s.title for s in sources}
        assert "valid1" in titles
        assert "valid2" in titles


# ===========================================================================
# 2. High-Volume Heterogeneous Batch Stress Tests
# ===========================================================================

class TestHighVolumeBatchStress:
    """Stress tests run_ingestion() with massive volume and mixed input types."""

    def test_high_volume_heterogeneous_batch(self, tmp_path):
        """Feed 100 heterogeneous sources (valid, invalid, corrupted, URLs) into run_ingestion."""
        assets_dir = tmp_path / "assets"
        sources_list = []

        # Create 40 valid markdown files with realistic technical content
        md_dir = tmp_path / "markdowns"
        md_dir.mkdir()
        for i in range(40):
            p = md_dir / f"doc_{i:03d}.md"
            p.write_text(f"""# Architectural Pattern {i}
This section explores V8 memory heaps and garbage collection invariants.
```javascript
function allocateHeapNode_{i}() {{
    const buffer = new ArrayBuffer(1024);
    return buffer;
}}
```
""")
            sources_list.append(str(p))

        # Create 15 zero-byte and corrupted files
        corrupt_dir = tmp_path / "corrupt"
        corrupt_dir.mkdir()
        for i in range(5):
            p = corrupt_dir / f"corrupt_{i}.pdf"
            p.write_bytes(b"bad pdf bytes")
            sources_list.append(str(p))
        for i in range(5):
            p = corrupt_dir / f"corrupt_{i}.pptx"
            p.write_bytes(b"bad pptx bytes")
            sources_list.append(str(p))
        for i in range(5):
            p = corrupt_dir / f"empty_{i}.png"
            p.write_bytes(b"")
            sources_list.append(str(p))

        # 20 non-existent paths
        for i in range(20):
            sources_list.append(f"/nonexistent/directory/path_{i}.pdf")

        # 10 invalid/malformed web URLs
        sources_list.extend([
            "http://invalid-non-existent-domain-12345.xyz/docs",
            "not_even_a_url",
            "ftp://unsupported-protocol.com/data",
            "   ",  # whitespace string
            "",      # empty string
        ])

        # 5 valid small in-memory generated PDFs
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        for i in range(5):
            doc = pymupdf.open()
            page = doc.new_page()
            page.insert_text((50, 50), f"PDF Document {i}: Event Loop Architecture")
            p_pdf = pdf_dir / f"valid_{i}.pdf"
            doc.save(str(p_pdf))
            doc.close()
            sources_list.append(str(p_pdf))

        out_corpus = tmp_path / "high_volume_corpus.json"

        start_time = time.time()
        # Mock requests to avoid slow external HTTP timeouts for the invalid URL
        with patch("scripts.ingestion.web_crawler.fetch_tier1_requests", return_value=(404, "")):
            with patch("scripts.ingestion.web_crawler.fetch_tier2_chrome", return_value=(1, "")):
                corpus = run_ingestion(sources_list, output_corpus_path=out_corpus, assets_dir=assets_dir)
        elapsed = time.time() - start_time

        # Validate that execution completed rapidly (< 15 seconds)
        assert elapsed < 15.0, f"Batch ingestion took too long: {elapsed:.2f}s"

        # Validate output corpus
        assert out_corpus.exists()
        raw_json = json.loads(out_corpus.read_text(encoding="utf-8"))
        assert_valid_corpus_contract(raw_json)

        # Expected successful sources: 40 markdowns + 5 empty images (which don't crash) + 5 valid PDFs + 1 web URL (crawl returns error page source) = 51 sources
        assert len(corpus.sources) >= 45
        # Verify code blocks extracted across batch
        all_code_blocks = [cb for s in corpus.sources for cb in s.extracted_code_blocks]
        assert len(all_code_blocks) >= 40
        # Topics should be aggregated
        assert len(corpus.aggregated_topics) > 0


# ===========================================================================
# 3. Schema Strictness & Resilience Oracles
# ===========================================================================

class TestSchemaStrictnessAndResilience:
    """Tests extreme edge states in UnifiedCorpus serialization and topic extraction."""

    def test_empty_corpus_schema_strictness(self, tmp_path):
        """Corpus with 0 sources must strictly conform to schema."""
        corpus = UnifiedCorpus()
        out_file = tmp_path / "empty_corpus.json"
        corpus.save(out_file)

        raw = json.loads(out_file.read_text(encoding="utf-8"))
        assert_valid_corpus_contract(raw)
        assert raw["sources"] == []
        assert raw["aggregated_topics"] == []

        # Roundtrip
        loaded = UnifiedCorpus.load(out_file)
        assert loaded.corpus_id == corpus.corpus_id
        assert len(loaded.sources) == 0

    def test_unicode_and_emojis_in_schema(self, tmp_path):
        """Corpus with multi-lingual Hinglish, Roman script, emojis, and math symbols."""
        corpus = UnifiedCorpus()
        source = IngestionSource(
            source_type="local_file",
            identifier="test/file.md",
            title="V8 Engine Internals & Memory Architecture 🚀 (Part I: Heap & Stack)",
            metadata={"notes": "Technically bolo toh, execution context create hota hai! 💯"},
        )
        source.add_chapter(
            title="Phase 1: Event Loop Tick Pipeline ⚡",
            text="Macro-tasks aur micro-tasks ke beech synchronization invariant maintain hota hai. ∑(t) <= 16.6ms.",
            start_time=0.0,
            end_time=120.5555,
        )
        source.add_code_block(
            code="const heapDump = { allocatedMB: 512, symbol: Symbol('λ') };",
            language="javascript",
        )
        source.add_image(
            path="assets/diagram.png",
            caption="Call stack state during Promise.withResolvers() call 📐",
            ocr_text="Stack Frame #1: main()",
        )
        corpus.add_source(source)

        out_file = tmp_path / "unicode_corpus.json"
        corpus.save(out_file)

        raw = json.loads(out_file.read_text(encoding="utf-8"))
        assert_valid_corpus_contract(raw)

        # Roundtrip fidelity check
        loaded = UnifiedCorpus.load(out_file)
        assert loaded.sources[0].title == source.title
        assert loaded.sources[0].chapters[0].start_time == 0.0
        assert loaded.sources[0].chapters[0].end_time == round(120.5555, 3)
        assert loaded.sources[0].extracted_code_blocks[0].code == source.extracted_code_blocks[0].code
        assert loaded.sources[0].extracted_images[0].caption == source.extracted_images[0].caption

    def test_topic_extraction_resilience_massive_chapters(self):
        """Topic extraction algorithm must handle high chapter volumes without degrading or crashing."""
        corpus = UnifiedCorpus()
        source = IngestionSource(
            source_type="local_file",
            identifier="benchmark.md",
            title="JavaScript Deep Dive",
        )
        # Add 500 chapters with varied technical tokens
        for i in range(500):
            source.add_chapter(
                title=f"Chapter {i}: MicrotaskQueue and GarbageCollection",
                text=f"The EventLoop executes MicrotaskQueue before next render tick. MemoryLeak prevention with WeakMap.",
            )
        corpus.add_source(source)

        topics = corpus.extract_topics()
        assert isinstance(topics, list)
        assert len(topics) <= 15
        assert len(topics) > 0
        # Expected high frequency technical keywords
        topics_lower = [t.lower() for t in topics]
        assert any(t in topics_lower for t in ["eventloop", "microtaskqueue", "weakmap", "garbagecollection"])

    def test_topic_extraction_punctuation_filtering_behavior(self):
        """Topic extraction on titles with punctuation-only tokens."""
        corpus = UnifiedCorpus()
        source = IngestionSource(
            source_type="local_file",
            identifier="empty.md",
            title="... --- !!! ???",
        )
        source.add_chapter(
            title="Clean Title",
            text="Clean chapter text about AsyncLocalStorage.",
        )
        corpus.add_source(source)
        topics = corpus.extract_topics()
        assert isinstance(topics, list)
        # Document empirical behavior: tokens with len > 2 and not numeric are returned
        assert "Clean" in topics or "Title" in topics or "AsyncLocalStorage" in topics


# ===========================================================================
# 4. Web Crawler Edge Cases & Adversarial HTML
# ===========================================================================

class TestAdversarialWebCrawler:
    """Stress tests HTML parsing, noise pruning, SPA detection, and tables."""

    def test_deeply_nested_html_recursion_resilience(self):
        """Adversarial HTML with 50 levels of deeply nested divs."""
        nested_html = "<div>" * 50 + "<h1>Deep Article</h1><p>Inside deep nesting.</p>" + "</div>" * 50
        md, code_blocks, title = html_to_markdown_and_code(nested_html)
        assert title == "Deep Article"
        assert "Deep Article" in md
        assert "Inside deep nesting." in md

    def test_malformed_html_tables_resilience(self):
        """Adversarial HTML tables with uneven rows, missing columns, and empty cells."""
        bad_table_html = """
        <table>
            <tr><th>Header 1</th><th>Header 2</th><th>Header 3</th></tr>
            <tr><td>Only one col</td></tr>
            <tr><td>Col 1</td><td>Col 2</td><td>Col 3</td><td>Extra Col 4</td></tr>
            <tr></tr>
        </table>
        """
        md, _, _ = html_to_markdown_and_code(bad_table_html)
        assert "| Header 1 | Header 2 | Header 3 |" in md
        # Should have padded or aligned columns without crashing
        assert "| --- |" in md

    def test_spa_detection_boundary_cases(self):
        """Test is_spa_shell() on subtle boundary cases."""
        # Clean static documentation with very short prose
        assert not is_spa_shell("<html><body><h1>Error 404</h1><p>The requested page was not found on this server.</p></body></html>")

        # Typical client-rendered React SPA skeleton
        assert is_spa_shell("<html><body><div id='root'></div><script src='/bundle.js'></script></body></html>")

        # Next.js SPA skeleton
        assert is_spa_shell("<html><body><div id='__next'></div><script src='/_next/static/chunks/main.js'></script></body></html>")

        # Completely empty HTML
        assert is_spa_shell("")
        assert is_spa_shell("   \n\t  ")

    def test_code_block_language_extraction_various_classes(self):
        """Ensure language classes like language-ts, lang-python, brush: js are parsed."""
        html = """
        <pre><code class="language-typescript">const x: number = 42;</code></pre>
        <pre class="lang-python"><code>def foo(): pass</code></pre>
        <pre><code>plain code</code></pre>
        """
        _, code_blocks, _ = html_to_markdown_and_code(html)
        assert len(code_blocks) == 3
        assert code_blocks[0].language == "typescript"
        assert code_blocks[1].language == "python"
        assert code_blocks[2].language == "text"


# ===========================================================================
# 5. YouTube & VTT Subtitle Edge Cases
# ===========================================================================

class TestYouTubeAdversarialVTT:
    """Stress tests VTT parser, timestamp conversions, and 3-line rolling deduplication."""

    def test_malformed_vtt_timestamps(self):
        """Handles non-standard timestamps, out-of-order cues, and missing headers."""
        malformed_vtt = """
        00:01.000 --> 00:03.000
        First line without hours.

        99:99:99.999 --> 100:00:00.000
        Extreme timestamp values.

        invalid --> invalid
        Skipped line.

        00:04:00.000 --> 00:05:00.000
        Valid timestamp cue.
        """
        cues = parse_vtt_cues(malformed_vtt)
        assert len(cues) >= 2
        assert cues[0]["start"] == 1.0
        assert cues[0]["end"] == 3.0
        assert "First line" in cues[0]["text"]

    def test_vtt_rolling_window_massive_repetitions(self):
        """Stress tests rolling-window deduplication against pathological repeated captions."""
        # 10 cues where each cue repeats the previous 2 lines and adds 1 new line
        cues = []
        for i in range(10):
            line_a = f"Line {i}"
            line_b = f"Line {i+1}"
            line_c = f"Line {i+2}"
            cues.append({
                "start": float(i * 3),
                "end": float((i + 1) * 3),
                "lines": [line_a, line_b, line_c],
                "raw_text": f"{line_a} {line_b} {line_c}",
                "text": f"{line_a} {line_b} {line_c}",
            })

        deduped = deduplicate_vtt_cues(cues)
        # Should not crash and should deduplicate repeated lines
        assert len(deduped) > 0
        emitted_text = " ".join(c["text"] for c in deduped)
        # Check that Line 0 is emitted once, Line 1 is emitted once, etc.
        assert emitted_text.count("Line 0") == 1

    def test_align_cues_to_chapters_without_metadata_or_long_duration(self):
        """Tests alignment when duration is long (> 900s) vs short (< 900s)."""
        cues = [
            {"start": 10.0, "end": 20.0, "text": "Beginning intro."},
            {"start": 1000.0, "end": 1020.0, "text": "Deep in the lecture."},
        ]

        # Case 1: Short video (duration = 100s) -> 1 single full transcript chapter
        short_chaps = align_cues_to_chapters(cues, raw_chapters=[], total_duration=100.0, video_title="Short Lecture")
        assert len(short_chaps) == 1
        assert "Beginning intro" in short_chaps[0].text

        # Case 2: Long video (duration = 1800s) -> synthesized segmented chapters
        long_chaps = align_cues_to_chapters(cues, raw_chapters=[], total_duration=1800.0, video_title="Long Lecture")
        assert len(long_chaps) >= 2


# ===========================================================================
# 6. Unified Runner Fault Isolation Oracle
# ===========================================================================

class TestUnifiedRunnerFaultIsolation:
    """Verifies that run_ingestion() never crashes or leaks exceptions to caller."""

    def test_runner_with_all_failing_local_inputs(self, tmp_path):
        """Calling run_ingestion() with completely non-existent local paths."""
        broken_sources = [
            "/path/that/does/not/exist/file1.pdf",
            "/path/that/does/not/exist/file2.pptx",
            "/path/that/does/not/exist/dir/",
            "",
            "   ",
        ]
        out_corpus = tmp_path / "failing_local_inputs_corpus.json"
        corpus = run_ingestion(broken_sources, output_corpus_path=out_corpus, assets_dir=tmp_path / "assets")

        assert isinstance(corpus, UnifiedCorpus)
        assert len(corpus.sources) == 0
        assert out_corpus.exists()
        raw = json.loads(out_corpus.read_text(encoding="utf-8"))
        assert_valid_corpus_contract(raw)

    def test_runner_with_unreachable_web_url_behavior(self, tmp_path):
        """Calling run_ingestion() with unreachable web URL produces structured error source."""
        out_corpus = tmp_path / "failing_web_inputs_corpus.json"
        corpus = run_ingestion(
            ["https://completely-unreachable-domain-xyz.com"],
            output_corpus_path=out_corpus,
            assets_dir=tmp_path / "assets",
        )

        assert isinstance(corpus, UnifiedCorpus)
        # Web crawler returns a structured failure IngestionSource
        assert len(corpus.sources) == 1
        assert "Failed to load" in corpus.sources[0].title
        assert out_corpus.exists()
        raw = json.loads(out_corpus.read_text(encoding="utf-8"))
        assert_valid_corpus_contract(raw)

    def test_runner_with_nested_nonexistent_output_directory(self, tmp_path):
        """Output corpus path specified in deeply nested non-existent directory."""
        nested_out = tmp_path / "deep" / "nested" / "dir" / "out_corpus.json"
        valid_file = tmp_path / "doc.md"
        valid_file.write_text("# Title\nContent.")

        corpus = run_ingestion([str(valid_file)], output_corpus_path=nested_out, assets_dir=tmp_path / "assets")
        assert nested_out.exists()
        assert len(corpus.sources) == 1


# ===========================================================================
# 7. Additional Adversarial Architectural Edge Cases
# ===========================================================================

class TestArchitecturalEdgeCasesAndOracles:
    """Stress tests boundary conditions across PPTX, YouTube playlists, and topics."""

    def test_youtube_playlist_partial_failure_resilience(self, tmp_path):
        """If one video in a playlist fails, other videos in the playlist must still be ingested."""
        fake_playlist_url = "https://www.youtube.com/playlist?list=PL123456789"
        mock_entries = [
            {"id": "vid1", "url": "https://www.youtube.com/watch?v=vid1", "title": "Vid 1"},
            {"id": "vid2", "url": "https://www.youtube.com/watch?v=vid2", "title": "Vid 2 (Broken)"},
            {"id": "vid3", "url": "https://www.youtube.com/watch?v=vid3", "title": "Vid 3"},
        ]

        def mock_ingest_video(url, **kwargs):
            if "vid2" in url:
                raise RuntimeError("yt-dlp download error: video is private or deleted")
            return IngestionSource(
                source_type="youtube",
                identifier=url,
                title=f"Title for {url}",
                metadata={"video_id": url.split("=")[-1]},
                chapters=[Chapter(1, "Main", 0.0, 10.0, "Content")],
            )

        with patch("scripts.ingestion.yt_ingest.extract_playlist_entries", return_value=mock_entries):
            with patch("scripts.ingestion.yt_ingest.ingest_youtube_video", side_effect=mock_ingest_video):
                from scripts.ingestion.yt_ingest import ingest_youtube_url as yt_ingest_url
                sources = yt_ingest_url(fake_playlist_url, output_dir=tmp_path)

        # 2 out of 3 videos must succeed, failure of vid2 must not abort the playlist
        assert len(sources) == 2
        assert sources[0].metadata["video_id"] == "vid1"
        assert sources[1].metadata["video_id"] == "vid3"

    def test_align_cues_to_chapters_boundary_drop_behavior(self):
        """Examine cue retention when cues fall before the first chapter or after the last chapter."""
        cues = [
            {"start": 5.0, "end": 8.0, "text": "Intro before first chapter"},
            {"start": 15.0, "end": 20.0, "text": "Inside chapter 1"},
            {"start": 75.0, "end": 80.0, "text": "Inside chapter 2"},
            {"start": 130.0, "end": 140.0, "text": "Outro after last chapter"},
        ]
        raw_chapters = [
            {"start_time": 10.0, "end_time": 60.0, "title": "Chapter 1: Foundations"},
            {"start_time": 60.0, "end_time": 120.0, "title": "Chapter 2: Advanced"},
        ]

        chaps = align_cues_to_chapters(cues, raw_chapters=raw_chapters, total_duration=150.0, video_title="Course")
        assert len(chaps) == 2
        # Verify matched cues inside defined interval
        assert "Inside chapter 1" in chaps[0].text
        assert "Inside chapter 2" in chaps[1].text
        # Note: cues outside defined chapter boundaries [10.0, 120.0) are unmapped

    def test_topic_extraction_with_url_titles(self):
        """When source title is a raw URL (common when <title> tag is missing), verify extracted topics."""
        corpus = UnifiedCorpus()
        source = IngestionSource(
            source_type="web",
            identifier="https://developer.mozilla.org/en-US/docs/Web/JavaScript/EventLoop",
            title="https://developer.mozilla.org/en-US/docs/Web/JavaScript/EventLoop",
        )
        source.add_chapter(
            title="Overview",
            text="JavaScript concurrency model has an EventLoop which executes tasks from the CallStack.",
        )
        corpus.add_source(source)
        topics = corpus.extract_topics()
        assert isinstance(topics, list)
        # Technical keywords from chapter text are captured
        topics_lower = [t.lower() for t in topics]
        assert any(t in topics_lower for t in ["eventloop", "callstack"])

