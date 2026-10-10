"""Ingestion Package for thenuke skill.

Exports core data models, extractors, and unified ingestion pipeline runner.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from .file_extract import (
    extract_directory,
    extract_image,
    extract_local_file,
    extract_media,
    extract_pdf,
    extract_pptx,
    extract_text_file,
    perform_apple_vision_ocr,
)
from .unified_corpus import (
    Chapter,
    CodeBlock,
    ExtractedImage,
    IngestionSource,
    UnifiedCorpus,
)
from .web_crawler import (
    crawl_url,
    find_chrome_binary,
    html_to_markdown_and_code,
)
from .yt_ingest import (
    align_cues_to_chapters,
    calculate_dynamic_frame_interval,
    clean_vtt_content,
    deduplicate_vtt_cues,
    download_youtube_video_720p,
    extract_high_density_frames,
    extract_playlist_entries,
    extract_video_id,
    extract_video_metadata,
    format_srt_timestamp,
    ingest_youtube_url,
    ingest_youtube_video,
    is_playlist_url,
    is_youtube_url,
    parse_vtt_cues,
    transcribe_audio_faster_whisper,
)

logger = logging.getLogger(__name__)


def run_ingestion(
    sources: List[str],
    output_corpus_path: Optional[str | Path] = "nuke_ingestion_corpus.json",
    assets_dir: Optional[str | Path] = "assets",
    download_video: bool = True,
    ocr_mode: bool = False,
) -> UnifiedCorpus:
    """Unified ingestion pipeline runner.
    
    Accepts arbitrary heterogeneous input sources (YouTube video/playlist URLs,
    Web documentation URLs, local files or directories), processes each through
    its specialized ingestion engine, and compiles into a UnifiedCorpus.
    """
    corpus = UnifiedCorpus()
    assets_path = Path(assets_dir) if assets_dir else Path("assets")
    assets_path.mkdir(parents=True, exist_ok=True)

    for src_str in sources:
        src = src_str.strip()
        if not src:
            continue

        try:
            # 1. YouTube URLs
            if is_youtube_url(src):
                logger.info(f"Ingesting YouTube source: {src} (download_video={download_video}, ocr_mode={ocr_mode})")
                yt_sources = ingest_youtube_url(
                    src,
                    output_dir=assets_path,
                    download_video=download_video,
                    ocr_mode=ocr_mode,
                )
                for s in yt_sources:
                    corpus.add_source(s)
                continue

            # 2. Web Documentation URLs
            if src.startswith(("http://", "https://")):
                logger.info(f"Ingesting Web source: {src}")
                web_src = crawl_url(src, output_dir=assets_path)
                corpus.add_source(web_src)
                continue

            # 3. Local Directory or File
            loc_path = Path(src).expanduser().resolve()
            if loc_path.is_dir():
                logger.info(f"Ingesting local directory: {loc_path}")
                dir_sources = extract_directory(loc_path, output_dir=assets_path, ocr_mode=ocr_mode)
                for s in dir_sources:
                    corpus.add_source(s)
            elif loc_path.is_file():
                logger.info(f"Ingesting local file: {loc_path}")
                f_src = extract_local_file(loc_path, output_dir=assets_path, ocr_mode=ocr_mode)
                corpus.add_source(f_src)
            else:
                logger.warning(f"Unrecognized or non-existent source target: {src}")

        except Exception as exc:
            logger.error(f"Error ingesting source '{src}': {exc}", exc_info=True)

    # Save corpus to file if output path specified
    if output_corpus_path:
        corpus.save(output_corpus_path)
        logger.info(f"Saved unified ingestion corpus to {output_corpus_path}")

    return corpus


__all__ = [
    # Models
    "UnifiedCorpus",
    "IngestionSource",
    "Chapter",
    "CodeBlock",
    "ExtractedImage",
    # Runner
    "run_ingestion",
    # YouTube
    "is_youtube_url",
    "is_playlist_url",
    "extract_video_id",
    "extract_video_metadata",
    "extract_playlist_entries",
    "parse_vtt_cues",
    "deduplicate_vtt_cues",
    "clean_vtt_content",
    "align_cues_to_chapters",
    "ingest_youtube_video",
    "ingest_youtube_url",
    "download_youtube_video_720p",
    "calculate_dynamic_frame_interval",
    "extract_high_density_frames",
    "format_srt_timestamp",
    "transcribe_audio_faster_whisper",
    # Web Crawler
    "crawl_url",
    "html_to_markdown_and_code",
    "find_chrome_binary",
    # Local File Extraction
    "extract_local_file",
    "extract_directory",
    "extract_pdf",
    "extract_pptx",
    "extract_media",
    "extract_image",
    "extract_text_file",
    "perform_apple_vision_ocr",
]
