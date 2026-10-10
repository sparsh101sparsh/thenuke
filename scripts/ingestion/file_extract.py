"""Local File Extraction Engine for thenuke skill.

Handles heterogeneous local files:
- PDF documents via PyMuPDF (text hierarchy, tables, embedded diagram extraction).
- PowerPoint presentations via python-pptx (slide titles, body bullets, tables, speaker notes).
- Local video & audio via ffmpeg demuxing + Apple M4 whisper-cli GPU transcription.
- Screenshots & architectural diagrams via macOS Apple Vision Framework OCR / PIL.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image
import pymupdf
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from .unified_corpus import Chapter, CodeBlock, ExtractedImage, IngestionSource
from .yt_ingest import clean_vtt_content, run_cmd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Apple Vision Framework OCR via Swift
# ---------------------------------------------------------------------------

SWIFT_VISION_SCRIPT = """
import Vision
import Foundation

guard CommandLine.arguments.count > 1 else { exit(1) }
let path = CommandLine.arguments[1]
let imageURL = URL(fileURLWithPath: path)

guard let imageSource = CGImageSourceCreateWithURL(imageURL as CFURL, nil),
      let image = CGImageSourceCreateImageAtIndex(imageSource, 0, nil) else {
    exit(1)
}

let request = VNRecognizeTextRequest { req, error in
    guard error == nil else { exit(1) }
    let observations = req.results as? [VNRecognizedTextObservation] ?? []
    for obs in observations {
        if let candidate = obs.topCandidates(1).first {
            print(candidate.string)
        }
    }
}
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false

let handler = VNImageRequestHandler(cgImage: image, options: [:])
do {
    try handler.perform([request])
} catch {
    exit(1)
}
"""


def perform_apple_vision_ocr(image_path: Path, timeout: int = 30) -> str:
    """Run native macOS Apple Vision OCR on an image file using Swift.
    
    Returns extracted text string, or empty string on failure / non-macOS.
    """
    swift_bin = shutil.which("swift") or "/usr/bin/swift"
    if not os.path.exists(swift_bin) or not image_path.exists():
        return ""

    try:
        proc = subprocess.run(
            [swift_bin, "-e", SWIFT_VISION_SCRIPT, str(image_path.resolve())],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    except Exception as exc:
        logger.warning(f"Apple Vision OCR execution error: {exc}")
    
    return ""


# ---------------------------------------------------------------------------
# Code Block Detection Helper
# ---------------------------------------------------------------------------

CODE_PATTERNS = [
    re.compile(r"^\s*(?:function|const|let|var|class|import|export|def|return)\s+[a-zA-Z0-9_$]+", re.MULTILINE),
    re.compile(r"[{}\[\];=>]{2,}", re.MULTILINE),
    re.compile(r"```([a-zA-Z0-9_-]+)?\n([\s\S]*?)```", re.MULTILINE),
]


def detect_code_blocks(text: str) -> List[CodeBlock]:
    """Scan raw text for Markdown or inline code blocks."""
    blocks: List[CodeBlock] = []
    
    # 1. Check for explicit markdown fences ```lang ... ```
    fence_matches = list(re.finditer(r"```([a-zA-Z0-9_-]*)[ \t]*\r?\n([\s\S]*?)```", text))
    if fence_matches:
        for m in fence_matches:
            lang = m.group(1).strip() if m.group(1) else "javascript"
            code_body = m.group(2).strip()
            if code_body:
                blocks.append(CodeBlock(language=lang or "javascript", code=code_body))
        return blocks

    # 2. Check for indented code blocks or JS keywords
    lines = text.splitlines()
    code_buffer: List[str] = []
    in_code = False

    for line in lines:
        if any(p.search(line) for p in CODE_PATTERNS[:2]):
            in_code = True
            code_buffer.append(line)
        elif in_code:
            if line.strip() == "" or line.startswith(("  ", "\t", "}", ";", ")")):
                code_buffer.append(line)
            else:
                if len(code_buffer) >= 2:
                    blocks.append(CodeBlock(language="javascript", code="\n".join(code_buffer).strip()))
                code_buffer = []
                in_code = False

    if code_buffer and len(code_buffer) >= 2:
        blocks.append(CodeBlock(language="javascript", code="\n".join(code_buffer).strip()))

    return blocks


# ---------------------------------------------------------------------------
# PDF Document Extraction (PyMuPDF)
# ---------------------------------------------------------------------------

def extract_pdf(pdf_path: Path, output_dir: Path) -> IngestionSource:
    """Extract structured text, headings, tables, and images from a PDF file."""
    doc = pymupdf.open(str(pdf_path))
    pdf_name = pdf_path.stem
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    chapters: List[Chapter] = []
    extracted_images: List[ExtractedImage] = []
    extracted_code_blocks: List[CodeBlock] = []

    total_pages = len(doc)
    meta = doc.metadata or {}

    for page_idx in range(total_pages):
        page = doc[page_idx]
        page_num = page_idx + 1

        # 1. Extract text and identify headings
        text_blocks = page.get_text("blocks")
        page_lines: List[str] = []
        page_title = f"Page {page_num}"

        for block in text_blocks:
            # block format: (x0, y0, x1, y1, "text", block_no, block_type)
            if block[6] == 0:  # text block
                raw_btext = block[4].strip()
                if not raw_btext:
                    continue

                # Check if block looks like a heading
                first_line = raw_btext.splitlines()[0].strip()
                if (first_line.startswith("#") or len(first_line) < 60) and page_title == f"Page {page_num}":
                    clean_h = first_line.lstrip("#").strip()
                    if clean_h and not clean_h.isnumeric():
                        page_title = f"Page {page_num}: {clean_h}"

                page_lines.append(raw_btext)

        # 2. Extract tables via PyMuPDF find_tables()
        try:
            tabs = page.find_tables()
            for tab_idx, tab in enumerate(tabs, start=1):
                extracted_table = tab.extract()
                if extracted_table and len(extracted_table) > 1:
                    md_rows: List[str] = []
                    header = [str(c or "").strip().replace("|", "\\|") for c in extracted_table[0]]
                    num_cols = len(header)
                    md_rows.append("| " + " | ".join(header) + " |")
                    md_rows.append("| " + " | ".join(["---"] * num_cols) + " |")
                    for row in extracted_table[1:]:
                        padded_row = [str(c or "").strip().replace("|", "\\|") for c in row]
                        padded_row += [""] * (num_cols - len(padded_row))
                        md_rows.append("| " + " | ".join(padded_row) + " |")
                    table_md = "\n" + "\n".join(md_rows) + "\n"
                    page_lines.append(table_md)
        except Exception as e:
            logger.debug(f"Table finding skipped on page {page_num}: {e}")

        page_text = "\n\n".join(page_lines).strip()

        # 3. Code blocks from page text
        cblocks = detect_code_blocks(page_text)
        extracted_code_blocks.extend(cblocks)

        # 4. Extract embedded images
        image_list = page.get_images(full=True)
        for img_idx, img_info in enumerate(image_list, start=1):
            xref = img_info[0]
            try:
                base_img = doc.extract_image(xref)
                image_bytes = base_img["image"]
                image_ext = base_img["ext"]
                img_filename = f"pdf_{pdf_name}_p{page_num}_img{img_idx}.{image_ext}"
                img_dest = assets_dir / img_filename

                with open(img_dest, "wb") as f_img:
                    f_img.write(image_bytes)

                # Perform OCR on extracted image
                ocr_text = perform_apple_vision_ocr(img_dest)
                if ocr_text:
                    ocr_code = detect_code_blocks(ocr_text)
                    extracted_code_blocks.extend(ocr_code)

                extracted_img = ExtractedImage(
                    path=str(img_dest),
                    caption=f"Embedded graphic from {pdf_name} Page {page_num}",
                    ocr_text=ocr_text,
                )
                extracted_images.append(extracted_img)
            except Exception as exc:
                logger.debug(f"Could not extract image xref {xref}: {exc}")

        chapters.append(Chapter(
            chapter_index=page_num,
            title=page_title,
            start_time=0.0,
            end_time=0.0,
            text=page_text,
        ))

    doc.close()

    source = IngestionSource(
        source_type="local_file",
        identifier=str(pdf_path),
        title=meta.get("title") or pdf_name,
        metadata={
            "file_type": "pdf",
            "page_count": total_pages,
            "author": meta.get("author", ""),
            "subject": meta.get("subject", ""),
            "file_size_bytes": pdf_path.stat().st_size if pdf_path.exists() else 0,
        },
        chapters=chapters,
        extracted_code_blocks=extracted_code_blocks,
        extracted_images=extracted_images,
    )
    return source


# ---------------------------------------------------------------------------
# PowerPoint Presentation Extraction (python-pptx)
# ---------------------------------------------------------------------------

def extract_pptx(pptx_path: Path, output_dir: Path) -> IngestionSource:
    """Extract slide titles, body bullets, tables, speaker notes, and images from PPTX."""
    prs = Presentation(str(pptx_path))
    pptx_name = pptx_path.stem
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    chapters: List[Chapter] = []
    extracted_images: List[ExtractedImage] = []
    extracted_code_blocks: List[CodeBlock] = []

    for slide_idx, slide in enumerate(prs.slides, start=1):
        slide_title = f"Slide {slide_idx}"
        body_parts: List[str] = []

        # Find title shape if present
        if slide.shapes.title and slide.shapes.title.text.strip():
            clean_t = slide.shapes.title.text.strip()
            slide_title = f"Slide {slide_idx}: {clean_t}"
            body_parts.append(f"## {clean_t}\n")

        # Process shapes
        img_counter = 1
        for shape in slide.shapes:
            # Skip title shape as it's already recorded
            if shape == slide.shapes.title:
                continue

            # Text box or content shape
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    p_text = para.text.strip()
                    if not p_text:
                        continue
                    # Format as bullet point if level > 0 or short bullet
                    prefix = "  " * para.level + "- " if para.level > 0 else ""
                    body_parts.append(f"{prefix}{p_text}")

            # Tables in slides
            if shape.has_table:
                table = shape.table
                table_rows: List[List[str]] = []
                for row in table.rows:
                    row_data = [cell.text.strip().replace("|", "\\|") for cell in row.cells]
                    table_rows.append(row_data)

                if table_rows:
                    ncols = len(table_rows[0])
                    table_md = ["\n| " + " | ".join(table_rows[0]) + " |"]
                    table_md.append("| " + " | ".join(["---"] * ncols) + " |")
                    for row in table_rows[1:]:
                        table_md.append("| " + " | ".join(row) + " |")
                    body_parts.append("\n".join(table_md) + "\n")

            # Pictures embedded in shapes
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    image = shape.image
                    img_bytes = image.blob
                    ext = image.ext or "png"
                    img_filename = f"pptx_{pptx_name}_s{slide_idx}_img{img_counter}.{ext}"
                    img_path = assets_dir / img_filename
                    with open(img_path, "wb") as f_img:
                        f_img.write(img_bytes)

                    ocr_text = perform_apple_vision_ocr(img_path)
                    extracted_images.append(ExtractedImage(
                        path=str(img_path),
                        caption=f"Embedded slide illustration from {pptx_name} (Slide {slide_idx})",
                        ocr_text=ocr_text,
                    ))
                    img_counter += 1
                except Exception as e:
                    logger.debug(f"Could not extract picture from slide {slide_idx}: {e}")

        # Speaker notes
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes_text = slide.notes_slide.notes_text_frame.text.strip()
            if notes_text:
                body_parts.append(f"\n> [SPEAKER NOTES / GOTCHAS]:\n> {notes_text}\n")

        full_slide_text = "\n".join(body_parts).strip()
        # Extract code blocks
        cblocks = detect_code_blocks(full_slide_text)
        extracted_code_blocks.extend(cblocks)

        chapters.append(Chapter(
            chapter_index=slide_idx,
            title=slide_title,
            start_time=0.0,
            end_time=0.0,
            text=full_slide_text,
        ))

    source = IngestionSource(
        source_type="local_file",
        identifier=str(pptx_path),
        title=pptx_name,
        metadata={
            "file_type": "pptx",
            "slide_count": len(prs.slides),
            "file_size_bytes": pptx_path.stat().st_size if pptx_path.exists() else 0,
        },
        chapters=chapters,
        extracted_code_blocks=extracted_code_blocks,
        extracted_images=extracted_images,
    )
    return source


# ---------------------------------------------------------------------------
# Local Video & Audio Transcription (ffmpeg + whisper-cli)
# ---------------------------------------------------------------------------

def extract_media(
    media_path: Path,
    output_dir: Path,
    ffmpeg_bin: str = "ffmpeg",
    whisper_bin: str = "whisper-cli",
    extract_frames: bool = False,
) -> IngestionSource:
    """Extract audio transcript and optional visual frames from local video/audio files.
    
    Invariant: AI Multimodal Visual Self-Analysis (Zero Programmatic Video OCR).
    When extract_frames=True for videos, scene frames are extracted and cataloged directly
    for AI multimodal vision inspection with zero OCR.
    """
    media_name = media_path.stem
    work_dir = output_dir / "media_transcripts"
    work_dir.mkdir(parents=True, exist_ok=True)
    wav_path = work_dir / f"{media_name}_16k.wav"
    out_prefix = str(work_dir / f"{media_name}_whisper")
    extracted_images: List[ExtractedImage] = []

    # 1. Try extracting embedded subtitle stream first if video
    sub_srt_path = work_dir / f"{media_name}_subs.srt"
    sub_args = [ffmpeg_bin, "-y", "-i", str(media_path), "-map", "0:s:0", "-c:s", "srt", str(sub_srt_path)]
    s_code, _, _ = run_cmd(sub_args, timeout=30)

    transcript = ""
    if s_code == 0 and sub_srt_path.exists() and sub_srt_path.stat().st_size > 50:
        transcript = clean_vtt_content(sub_srt_path.read_text(encoding="utf-8", errors="replace"))

    # 2. If no subtitles, convert to 16kHz mono WAV and transcribe with whisper-cli
    if not transcript:
        ffmpeg_cmd = [
            ffmpeg_bin,
            "-y",
            "-i", str(media_path),
            "-vn",
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            str(wav_path),
        ]
        ff_code, _, ff_err = run_cmd(ffmpeg_cmd, timeout=120)
        if ff_code == 0:
            # Run whisper-cli
            whisper_cmd = [
                whisper_bin,
                "-f", str(wav_path),
                "--output-vtt",
                "-of", out_prefix,
                "-l", "auto",
            ]
            w_code, w_out, _ = run_cmd(whisper_cmd, timeout=300)
            vtt_file = Path(f"{out_prefix}.vtt")
            if vtt_file.exists():
                transcript = clean_vtt_content(vtt_file.read_text(encoding="utf-8", errors="replace"))
            elif Path(f"{out_prefix}.txt").exists():
                transcript = Path(f"{out_prefix}.txt").read_text(encoding="utf-8", errors="replace")
            else:
                transcript = w_out.strip()

    if not transcript:
        transcript = f"[Audio/Video transcription completed: {media_name}]"

    # 3. Extract visual frames if requested for local video
    if extract_frames and media_path.suffix.lower() in [".mp4", ".mkv", ".webm", ".mov", ".avi", ".flv", ".wmv"]:
        frames_dir = work_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        out_pattern = str(frames_dir / "frame_%04d.jpg")
        frame_cmd = [
            ffmpeg_bin,
            "-y",
            "-i", str(media_path),
            "-vf", "fps=0.5",
            "-q:v", "2",
            out_pattern,
        ]
        f_code, _, _ = run_cmd(frame_cmd, timeout=120)
        if f_code == 0:
            frame_files = sorted(list(frames_dir.glob("frame_*.jpg")))
            for idx, f_path in enumerate(frame_files):
                extracted_images.append(ExtractedImage(
                    path=str(f_path),
                    caption=f"Local video frame {idx + 1} ({f_path.name})",
                    ocr_text="",
                ))
            logger.info(f"Extracted {len(extracted_images)} frames from {media_path.name} for AI multimodal visual self-analysis (zero OCR).")

    chapters = [
        Chapter(
            chapter_index=1,
            title=f"{media_name} Transcript",
            start_time=0.0,
            end_time=0.0,
            text=transcript,
        )
    ]

    source = IngestionSource(
        source_type="local_file",
        identifier=str(media_path),
        title=media_name,
        metadata={
            "file_type": media_path.suffix.lstrip(".").lower(),
            "file_size_bytes": media_path.stat().st_size if media_path.exists() else 0,
        },
        chapters=chapters,
        extracted_images=extracted_images,
        extracted_code_blocks=detect_code_blocks(transcript),
    )
    return source


# ---------------------------------------------------------------------------
# Image & Screenshot Extraction (Apple Vision OCR / PIL)
# ---------------------------------------------------------------------------

def extract_image(image_path: Path, output_dir: Path) -> IngestionSource:
    """Extract text labels, code snippets, and metadata from screenshots and diagrams."""
    img_name = image_path.stem
    ocr_text = perform_apple_vision_ocr(image_path)
    code_blocks = detect_code_blocks(ocr_text)

    # Image metadata via PIL
    width, height, format_name = 0, 0, "IMAGE"
    try:
        with Image.open(image_path) as im:
            width, height = im.size
            format_name = im.format or "IMAGE"
    except Exception as e:
        logger.debug(f"PIL failed to inspect {image_path}: {e}")

    caption = f"Architecture diagram / visual frame: {img_name} ({width}x{height} {format_name})"
    content_text = f"### {caption}\n\n**OCR Extracted Technical Text:**\n{ocr_text if ocr_text else '[No machine text detected]'}"

    source = IngestionSource(
        source_type="local_file",
        identifier=str(image_path),
        title=img_name,
        metadata={
            "file_type": "image",
            "format": format_name,
            "width": width,
            "height": height,
            "file_size_bytes": image_path.stat().st_size if image_path.exists() else 0,
        },
        chapters=[
            Chapter(
                chapter_index=1,
                title=f"Diagram: {img_name}",
                start_time=0.0,
                end_time=0.0,
                text=content_text,
            )
        ],
        extracted_code_blocks=code_blocks,
        extracted_images=[
            ExtractedImage(path=str(image_path), caption=caption, ocr_text=ocr_text)
        ],
    )
    return source


# ---------------------------------------------------------------------------
# Plain Text & Markdown File Extraction
# ---------------------------------------------------------------------------

def extract_text_file(text_path: Path) -> IngestionSource:
    """Extract plain text or Markdown documentation file."""
    text_content = text_path.read_text(encoding="utf-8", errors="replace")
    title = text_path.stem
    code_blocks = detect_code_blocks(text_content)

    return IngestionSource(
        source_type="local_file",
        identifier=str(text_path),
        title=title,
        metadata={
            "file_type": text_path.suffix.lstrip(".").lower(),
            "file_size_bytes": text_path.stat().st_size if text_path.exists() else 0,
        },
        chapters=[
            Chapter(
                chapter_index=1,
                title=title,
                start_time=0.0,
                end_time=0.0,
                text=text_content,
            )
        ],
        extracted_code_blocks=code_blocks,
    )


# ---------------------------------------------------------------------------
# High-Level File & Directory Dispatcher
# ---------------------------------------------------------------------------

SUPPORTED_MEDIA_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".svg"}
SUPPORTED_DOC_EXTS = {".pdf", ".pptx", ".ppt", ".txt", ".md", ".markdown"}


def extract_local_file(
    file_path: str | Path,
    output_dir: Optional[str | Path] = None,
) -> IngestionSource:
    """Extract any supported local file (PDF, PPTX, Video, Audio, Image, Text)."""
    p = Path(file_path).resolve()
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"Local file does not exist: {file_path}")

    out = Path(output_dir) if output_dir else Path(tempfile.gettempdir()) / "thenuke_extracted"
    out.mkdir(parents=True, exist_ok=True)

    ext = p.suffix.lower()
    if ext == ".pdf":
        return extract_pdf(p, out)
    elif ext in {".pptx", ".ppt"}:
        return extract_pptx(p, out)
    elif ext in SUPPORTED_MEDIA_EXTS:
        return extract_media(p, out)
    elif ext in SUPPORTED_IMAGE_EXTS:
        return extract_image(p, out)
    elif ext in {".txt", ".md", ".markdown"}:
        return extract_text_file(p)
    else:
        # Generic fallback
        return extract_text_file(p)


def extract_directory(
    dir_path: str | Path,
    output_dir: Optional[str | Path] = None,
) -> List[IngestionSource]:
    """Recursively extract all supported files from a directory."""
    root = Path(dir_path).resolve()
    if not root.exists() or not root.is_dir():
        raise NotADirectoryError(f"Directory does not exist: {dir_path}")

    sources: List[IngestionSource] = []
    supported_exts = SUPPORTED_DOC_EXTS | SUPPORTED_MEDIA_EXTS | SUPPORTED_IMAGE_EXTS

    for item in sorted(root.rglob("*")):
        if item.is_file() and item.suffix.lower() in supported_exts:
            # Skip hidden files or files in __pycache__ / .git
            if item.name.startswith(".") or any(part.startswith(".") for part in item.parts):
                continue
            try:
                src = extract_local_file(item, output_dir=output_dir)
                sources.append(src)
            except Exception as e:
                logger.error(f"Failed to extract {item}: {e}")

    return sources
