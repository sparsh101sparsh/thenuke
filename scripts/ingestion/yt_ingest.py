"""YouTube Video and Playlist Ingestion Engine for thenuke skill.

Handles YouTube video and playlist URL ingestion, metadata extraction,
subtitle download (manual and auto-generated), rolling-window 3-line VTT
caption deduplication, audio demuxing via ffmpeg, and Apple Silicon
whisper-cli transcription fallback.
"""

from __future__ import annotations

import html
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from .unified_corpus import Chapter, CodeBlock, ExtractedImage, IngestionSource

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# URL Validation & Helper Functions
# ---------------------------------------------------------------------------

def is_youtube_url(url: str) -> bool:
    """Check if the provided string is a valid YouTube video or playlist URL."""
    if not url or not isinstance(url, str):
        return False
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    return host in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "music.youtube.com",
    }


def is_playlist_url(url: str) -> bool:
    """Check if the URL points to a YouTube playlist."""
    if not is_youtube_url(url):
        return False
    parsed = urlparse(url.strip())
    qs = parse_qs(parsed.query)
    if "list" in qs:
        # If it has list=, check if it is not just a mix or search
        playlist_id = qs["list"][0]
        # Ignore radio mixes like RD... unless explicitly requested
        return bool(playlist_id and not playlist_id.startswith("RDMM"))
    return "/playlist" in parsed.path.lower()


def extract_video_id(url: str) -> Optional[str]:
    """Extract the standard 11-character YouTube video ID."""
    if not is_youtube_url(url):
        return None
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    if host == "youtu.be":
        # Short URL: https://youtu.be/<video_id>
        parts = parsed.path.strip("/").split("/")
        return parts[0] if parts and len(parts[0]) == 11 else None
    
    qs = parse_qs(parsed.query)
    if "v" in qs and qs["v"]:
        return qs["v"][0]
    
    # Path formats like /embed/<id> or /v/<id>
    path_parts = [p for p in parsed.path.split("/") if p]
    if len(path_parts) >= 2 and path_parts[0] in {"embed", "v", "shorts"}:
        return path_parts[1]
    
    return None


# ---------------------------------------------------------------------------
# VTT Parsing & 3-Line Rolling Window Deduplication
# ---------------------------------------------------------------------------

def parse_timestamp_seconds(ts_str: str) -> float:
    """Convert a VTT or SRT timestamp string (HH:MM:SS.mmm or MM:SS.mmm) to seconds."""
    ts_str = ts_str.strip().replace(",", ".")
    parts = ts_str.split(":")
    try:
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        else:
            return float(parts[0])
    except (ValueError, TypeError):
        return 0.0


def format_seconds_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS string."""
    seconds = max(0.0, float(seconds))
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"


# Regex matching valid WebVTT and HTML style tags while preserving code comparisons and generics
VTT_STYLE_TAG_PATTERN = re.compile(
    r"</?(?:c(?:\.[a-zA-Z0-9_.-]+)*|v(?:\.[a-zA-Z0-9_.-]+)?(?:\s+[^>]*)?|lang(?:\s+[^>]*)?|b|i|u|ruby|rt|font(?:\s+[^>]*)?)(?:\s+[^>]*)?>",
    re.IGNORECASE,
)


def strip_vtt_markup(text: str) -> str:
    """Remove HTML/VTT micro-cues, inline timestamps, voice tags, and entity references.
    
    Preserves programming comparisons (e.g. `x < 10 and y > 20`) and generics (`Promise<Response>`).
    """
    if not text:
        return ""
    # Remove timestamps inside cues like <00:01:23.456>
    cleaned = re.sub(r"<\d{1,2}:\d{2}(?::\d{2})?(?:\.\d{1,3})?>", "", text)
    # Remove only legitimate WebVTT formatting/voice/class tags
    cleaned = VTT_STYLE_TAG_PATTERN.sub("", cleaned)
    # Unescape HTML entities
    cleaned = html.unescape(cleaned)
    # Normalize spaces
    cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()
    return cleaned


def parse_vtt_cues(vtt_content: str) -> List[Dict[str, Any]]:
    """Parse raw WebVTT content into a list of cue dictionaries.
    
    Each cue dict contains:
    - 'start': float (start time in seconds)
    - 'end': float (end time in seconds)
    - 'lines': List[str] (cleaned text lines)
    - 'raw_text': str
    """
    cues: List[Dict[str, Any]] = []
    lines = vtt_content.splitlines()
    
    # Regex for VTT timestamp line: 00:00:01.000 --> 00:00:04.000
    time_pattern = re.compile(
        r"((?:\d{1,2}:)?\d{2}:\d{2}[.,]\d{3})\s+-->\s+((?:\d{1,2}:)?\d{2}:\d{2}[.,]\d{3})"
    )

    current_start: Optional[float] = None
    current_end: Optional[float] = None
    current_lines: List[str] = []

    for idx, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean:
            if current_start is not None and current_lines:
                text_clean = " ".join(current_lines).strip()
                if text_clean:
                    cues.append({
                        "start": current_start,
                        "end": current_end or (current_start + 1.0),
                        "lines": list(current_lines),
                        "raw_text": text_clean,
                        "text": text_clean,
                    })
                current_start = None
                current_end = None
                current_lines = []
            continue

        # Check for header
        if line_clean.startswith("WEBVTT") or line_clean.startswith("NOTE"):
            continue

        # Check for timestamp
        match = time_pattern.search(line_clean)
        if match:
            # If we had a pending cue, flush it
            if current_start is not None and current_lines:
                text_clean = " ".join(current_lines).strip()
                if text_clean:
                    cues.append({
                        "start": current_start,
                        "end": current_end or (current_start + 1.0),
                        "lines": list(current_lines),
                        "raw_text": text_clean,
                        "text": text_clean,
                    })
                current_lines = []
            current_start = parse_timestamp_seconds(match.group(1))
            current_end = parse_timestamp_seconds(match.group(2))
        else:
            # Text line (or cue identifier line before timestamp)
            if current_start is not None:
                # Lookahead: If line is an integer cue number followed by a timestamp line,
                # flush the pending cue and discard this cue number from cue text.
                if line_clean.isdigit():
                    is_next_timestamp = False
                    for next_idx in range(idx + 1, len(lines)):
                        next_line_clean = lines[next_idx].strip()
                        if not next_line_clean:
                            continue
                        if time_pattern.search(next_line_clean):
                            is_next_timestamp = True
                        break

                    if is_next_timestamp:
                        text_clean = " ".join(current_lines).strip()
                        if text_clean:
                            cues.append({
                                "start": current_start,
                                "end": current_end or (current_start + 1.0),
                                "lines": list(current_lines),
                                "raw_text": text_clean,
                                "text": text_clean,
                            })
                        current_start = None
                        current_end = None
                        current_lines = []
                        continue

                stripped = strip_vtt_markup(line_clean)
                if stripped:
                    current_lines.append(stripped)

    # Flush final cue
    if current_start is not None and current_lines:
        text_clean = " ".join(current_lines).strip()
        if text_clean:
            cues.append({
                "start": current_start,
                "end": current_end or (current_start + 1.0),
                "lines": list(current_lines),
                "raw_text": text_clean,
                "text": text_clean,
            })

    return cues


def deduplicate_vtt_cues(cues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate YouTube auto-generated captions using a rolling-window 3-line filter.
    
    YouTube auto-generated VTT subtitles continuously shift a 2 to 3 line window.
    For example:
      Cue 1: ["Hello and welcome", "to this lecture"]
      Cue 2: ["to this lecture", "on JavaScript internals"]
      Cue 3: ["on JavaScript internals", "and the V8 engine"]
      
    This algorithm tracks recently emitted lines and tokens, removing overlapping
    prefix lines from subsequent cues to produce a clean linear narrative stream.
    """
    if not cues:
        return []

    cleaned_cues: List[Dict[str, Any]] = []
    emitted_lines_window: List[str] = []
    max_window_size = 5

    for cue in cues:
        cue_lines = [line.strip() for line in cue.get("lines", []) if line.strip()]
        if not cue_lines:
            continue

        new_lines: List[str] = []
        for line in cue_lines:
            # Check if this exact line was recently emitted in the window
            normalized_line = line.lower()
            if any(normalized_line == prev.lower() for prev in emitted_lines_window):
                continue
            
            # Check if the line is a partial suffix or progressive prefix of the last emitted line
            if emitted_lines_window:
                last_line = emitted_lines_window[-1]
                last_norm = last_line.lower()

                # Suffix check with word boundary: ignore if line is merely the trailing portion of the previous line
                if (last_norm.endswith(" " + normalized_line) or last_norm.startswith(normalized_line + " ")) and len(normalized_line) < len(last_norm):
                    continue

                # Progressive caption check: line extends last emitted line by adding new words
                is_prefix = normalized_line.startswith(last_norm + " ") or (
                    normalized_line.startswith(last_norm)
                    and len(normalized_line) > len(last_norm)
                    and normalized_line[len(last_norm)] in " ,.!?;:-"
                )
                if is_prefix:
                    # Update the existing prior cue in place to avoid stutter duplication
                    if cleaned_cues and not new_lines:
                        cleaned_cues[-1]["text"] = line
                        cleaned_cues[-1]["end"] = max(cleaned_cues[-1]["end"], cue.get("end", cleaned_cues[-1]["end"]))
                        emitted_lines_window[-1] = line
                        continue
                    elif new_lines:
                        new_lines[-1] = line
                        emitted_lines_window[-1] = line
                        continue

            new_lines.append(line)
            emitted_lines_window.append(line)
            if len(emitted_lines_window) > max_window_size:
                emitted_lines_window.pop(0)

        if new_lines:
            cue_text = " ".join(new_lines).strip()
            if cue_text:
                cleaned_cues.append({
                    "start": cue["start"],
                    "end": cue["end"],
                    "text": cue_text,
                })

    return cleaned_cues


def clean_vtt_content(vtt_content: str) -> str:
    """High-level function to parse raw VTT and return clean continuous text."""
    cues = parse_vtt_cues(vtt_content)
    deduped = deduplicate_vtt_cues(cues)
    
    # Merge deduped cues into readable paragraphs
    paragraphs: List[str] = []
    curr_para: List[str] = []
    last_end = 0.0

    for cue in deduped:
        text = cue["text"]
        # If silence pause > 2.5 seconds or end of sentence, break paragraph
        if curr_para and (cue["start"] - last_end > 2.5 or curr_para[-1].endswith((".", "!", "?"))):
            paragraphs.append(" ".join(curr_para))
            curr_para = [text]
        else:
            curr_para.append(text)
        last_end = cue["end"]

    if curr_para:
        paragraphs.append(" ".join(curr_para))

    return "\n\n".join(paragraphs)


# ---------------------------------------------------------------------------
# Chapter Alignment
# ---------------------------------------------------------------------------

def align_cues_to_chapters(
    cues: List[Dict[str, Any]],
    raw_chapters: List[Dict[str, Any]],
    total_duration: float = 0.0,
    video_title: str = "Video Content",
) -> List[Chapter]:
    """Align subtitle cues into coherent Chapter objects based on video timestamps.
    
    If raw_chapters are provided (from YouTube metadata), cues are allocated to
    each chapter interval [start_time, end_time).
    If no chapters exist, creates a structured single or multi-part division.
    """
    if not raw_chapters:
        # Synthesize chapters if total_duration is long (> 15 mins = 900s)
        full_text = "\n\n".join(c["text"] for c in cues) if cues else ""
        if total_duration > 900 and cues:
            # Segment into ~10 minute intervals
            segment_len = 600.0
            synthesized: List[Chapter] = []
            seg_idx = 1
            curr_t = 0.0
            while curr_t < total_duration:
                next_t = min(curr_t + segment_len, total_duration)
                seg_cues = [c for c in cues if curr_t <= c["start"] < next_t]
                seg_text = " ".join(c["text"] for c in seg_cues)
                if seg_text.strip():
                    synthesized.append(Chapter(
                        chapter_index=seg_idx,
                        title=f"{video_title} (Part {seg_idx} - {format_seconds_timestamp(curr_t)})",
                        start_time=curr_t,
                        end_time=next_t,
                        text=seg_text.strip(),
                    ))
                    seg_idx += 1
                curr_t = next_t
            if synthesized:
                return synthesized

        # Single chapter default
        return [
            Chapter(
                chapter_index=1,
                title=f"{video_title} - Full Transcript",
                start_time=0.0,
                end_time=float(total_duration),
                text=full_text,
            )
        ]

    # Map cues to given chapters
    chapters: List[Chapter] = []
    for idx, chap_meta in enumerate(raw_chapters, start=1):
        start_t = float(chap_meta.get("start_time", 0.0))
        end_t = float(chap_meta.get("end_time", start_t + 60.0))
        title = chap_meta.get("title", f"Chapter {idx}")

        # Find matching cues
        matched_cues = [c for c in cues if start_t <= c["start"] < end_t]
        chapter_text = " ".join(c["text"] for c in matched_cues).strip()

        chapters.append(Chapter(
            chapter_index=idx,
            title=title,
            start_time=start_t,
            end_time=end_t,
            text=chapter_text,
        ))

    return chapters


# ---------------------------------------------------------------------------
# yt-dlp & Subprocess Execution
# ---------------------------------------------------------------------------

def run_cmd(args: List[str], timeout: int = 120) -> Tuple[int, str, str]:
    """Execute a system command and return (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as exc:
        logger.error(f"Error running command {args}: {exc}")
        return 1, "", str(exc)


def extract_video_metadata(url: str, yt_dlp_bin: str = "yt-dlp") -> Dict[str, Any]:
    """Extract full JSON metadata for a YouTube video using yt-dlp."""
    args = [yt_dlp_bin, "--dump-json", "--skip-download", "--no-warnings", url]
    code, stdout, stderr = run_cmd(args, timeout=60)
    if code != 0 or not stdout.strip():
        raise RuntimeError(f"yt-dlp failed to extract metadata for {url}: {stderr}")
    
    # Parse JSON
    return json.loads(stdout.strip().splitlines()[0])


def extract_playlist_entries(url: str, yt_dlp_bin: str = "yt-dlp") -> List[Dict[str, Any]]:
    """Extract flat playlist entries (title, id, url) without downloading videos."""
    args = [
        yt_dlp_bin,
        "--dump-json",
        "--flat-playlist",
        "--skip-download",
        "--no-warnings",
        url,
    ]
    code, stdout, stderr = run_cmd(args, timeout=90)
    if code != 0 or not stdout.strip():
        raise RuntimeError(f"yt-dlp failed to inspect playlist {url}: {stderr}")
    
    entries = []
    for line in stdout.strip().splitlines():
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def download_subtitles(
    url: str,
    output_dir: Path,
    yt_dlp_bin: str = "yt-dlp",
) -> Optional[Path]:
    """Download best English or Hindi subtitle file (manual or auto-generated VTT/SRT).
    
    Returns the path to the downloaded subtitle file, or None if no subtitle found.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(output_dir / "%(id)s.%(ext)s")
    
    args = [
        yt_dlp_bin,
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs", "hi-orig,hi,en,en.*,hi.*",
        "--sub-format", "vtt/srt/best",
        "-o", out_template,
        url,
    ]
    code, _, stderr = run_cmd(args, timeout=90)
    
    # Look for downloaded subtitle files in output_dir
    sub_files = list(output_dir.glob("*.vtt")) + list(output_dir.glob("*.srt"))
    if sub_files:
        # Prefer manual English over auto, and VTT over SRT
        def sub_priority(p: Path) -> int:
            name = p.name.lower()
            score = 0
            if ".vtt" in name:
                score += 10
            if "en" in name:
                score += 5
            if "auto" not in name:
                score += 20
            return score
        
        sub_files.sort(key=sub_priority, reverse=True)
        return sub_files[0]
    
    return None


def download_youtube_video_720p(
    url: str,
    output_dir: Path,
    yt_dlp_bin: str = "yt-dlp",
) -> Optional[Path]:
    """Download YouTube video at strictly 720p maximum resolution.
    
    Uses yt-dlp format specification:
    -f "bestvideo[height<=720]+bestaudio/best[height<=720]"
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(output_dir / "%(id)s.%(ext)s")
    
    args = [
        yt_dlp_bin,
        "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "--no-playlist",
        "--no-warnings",
        "-o", out_template,
        url,
    ]
    code, _, stderr = run_cmd(args, timeout=300)
    if code != 0:
        logger.warning(f"720p video download failed for {url}: {stderr}")
        return None
    
    # Check for downloaded video file matching video_id first
    vid_id = extract_video_id(url)
    if vid_id:
        for ext in ("*.mp4", "*.mkv", "*.webm", "*.m4v"):
            candidates = [p for p in output_dir.glob(ext) if vid_id in p.name]
            if candidates:
                return candidates[0]

    # Fallback to general candidate scanning
    for ext in ("*.mp4", "*.mkv", "*.webm", "*.m4v"):
        candidates = list(output_dir.glob(ext))
        if candidates:
            return candidates[0]
            
    return None


def calculate_dynamic_frame_interval(duration_seconds: float) -> float:
    """Calculate extraction interval (seconds per frame) based on video length.
    
    High density strategy for capturing whiteboard text, slides, code changes, and UI demos:
    - <= 2 mins (120s): 1.0s interval (1.0 fps)
    - 2-10 mins (600s): 2.0s interval (0.5 fps)
    - 10-30 mins (1800s): 5.0s interval (0.2 fps)
    - 30-60 mins (3600s): 10.0s interval (0.1 fps)
    - > 60 mins: 20.0s interval (0.05 fps)
    """
    duration = max(1.0, float(duration_seconds))
    if duration <= 120.0:
        return 1.0
    elif duration <= 600.0:
        return 2.0
    elif duration <= 1800.0:
        return 5.0
    elif duration <= 3600.0:
        return 10.0
    else:
        return 20.0


def extract_high_density_frames(
    video_path: Path,
    output_dir: Path,
    duration_seconds: float,
    ffmpeg_bin: str = "ffmpeg",
) -> List[Path]:
    """Extract high-density video frames via ffmpeg at dynamically calculated rate."""
    output_dir.mkdir(parents=True, exist_ok=True)
    interval = calculate_dynamic_frame_interval(duration_seconds)
    fps_val = 1.0 / interval
    out_pattern = str(output_dir / "frame_%04d.jpg")

    args = [
        ffmpeg_bin,
        "-y",
        "-i", str(video_path),
        "-vf", f"fps={fps_val:.4f}",
        "-q:v", "2",
        out_pattern,
    ]
    code, _, stderr = run_cmd(args, timeout=300)
    if code != 0:
        logger.warning(f"ffmpeg frame extraction failed for {video_path}: {stderr}")
        return []

    frames = sorted(list(output_dir.glob("frame_*.jpg")))
    return frames


def format_srt_timestamp(seconds: float) -> str:
    """Format seconds into standard SRT timestamp HH:MM:SS,mmm."""
    seconds = max(0.0, float(seconds))
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def transcribe_audio_faster_whisper(
    audio_path: Path,
    output_dir: Path,
    model_size: str = "large-v3-turbo",
    device: str = "auto",
    compute_type: str = "default",
) -> Tuple[Optional[Path], str]:
    """Transcribe audio using faster-whisper (large-v3-turbo) and output timestamped .srt.
    
    Returns:
        (srt_file_path, full_transcript_text)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    srt_path = output_dir / f"{audio_path.stem}_transcript.srt"

    try:
        from faster_whisper import WhisperModel

        logger.info(f"Loading faster-whisper model '{model_size}' (device={device})...")
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        segments, info = model.transcribe(str(audio_path), beam_size=5)

        srt_lines: List[str] = []
        transcript_parts: List[str] = []

        for idx, seg in enumerate(segments, start=1):
            start_str = format_srt_timestamp(seg.start)
            end_str = format_srt_timestamp(seg.end)
            text_str = seg.text.strip()
            srt_lines.append(f"{idx}\n{start_str} --> {end_str}\n{text_str}\n")
            transcript_parts.append(text_str)

        srt_content = "\n".join(srt_lines)
        srt_path.write_text(srt_content, encoding="utf-8")
        full_transcript = " ".join(transcript_parts).strip()
        logger.info(f"faster-whisper transcribed {len(srt_lines)} segments to {srt_path}")
        return srt_path, full_transcript

    except Exception as exc:
        logger.warning(f"faster-whisper execution failed: {exc}")
        return None, ""


def transcribe_audio_fallback(
    url_or_file: str,
    output_dir: Path,
    ffmpeg_bin: str = "ffmpeg",
    whisper_bin: str = "whisper-cli",
    model_size: str = "large-v3-turbo",
) -> str:
    """Fallback audio transcription pipeline using ffmpeg + faster-whisper (large-v3-turbo)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    wav_path = output_dir / "temp_audio_16k.wav"

    # Step 1: ffmpeg demuxing to 16kHz mono WAV
    ffmpeg_args = [
        ffmpeg_bin,
        "-y",
        "-i", url_or_file,
        "-vn",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(wav_path),
    ]
    code, _, err = run_cmd(ffmpeg_args, timeout=180)
    if code != 0 or not wav_path.exists():
        logger.warning(f"ffmpeg audio conversion failed: {err}")
        return ""

    # Step 2: faster-whisper with large-v3-turbo and .srt output
    srt_path, transcript = transcribe_audio_faster_whisper(
        wav_path,
        output_dir,
        model_size=model_size,
    )
    if srt_path and srt_path.exists() and transcript:
        return transcript

    # Step 3: Metal GPU whisper-cli fallback if faster-whisper is unavailable
    out_prefix = str(output_dir / "whisper_transcript")
    whisper_args = [
        whisper_bin,
        "-f", str(wav_path),
        "--output-vtt",
        "-of", out_prefix,
        "-l", "auto",
    ]
    w_code, out, _ = run_cmd(whisper_args, timeout=300)
    vtt_candidate = Path(f"{out_prefix}.vtt")
    txt_candidate = Path(f"{out_prefix}.txt")

    if vtt_candidate.exists():
        vtt_text = vtt_candidate.read_text(encoding="utf-8", errors="replace")
        return clean_vtt_content(vtt_text)
    elif txt_candidate.exists():
        return txt_candidate.read_text(encoding="utf-8", errors="replace")
    
    return out.strip()


# ---------------------------------------------------------------------------
# High-Level Ingestion Entry Points
# ---------------------------------------------------------------------------

def ingest_youtube_video(
    url: str,
    output_dir: Optional[str | Path] = None,
    yt_dlp_bin: str = "yt-dlp",
    ffmpeg_bin: str = "ffmpeg",
    whisper_bin: str = "whisper-cli",
    download_video: bool = True,
) -> IngestionSource:
    """Ingest a single YouTube video, returning an IngestionSource object."""
    if not is_youtube_url(url):
        raise ValueError(f"Invalid YouTube URL: {url}")

    temp_dir_obj = None
    if output_dir:
        work_dir = Path(output_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
    else:
        temp_dir_obj = tempfile.TemporaryDirectory()
        work_dir = Path(temp_dir_obj.name)

    try:
        # 1. Fetch metadata
        meta = extract_video_metadata(url, yt_dlp_bin=yt_dlp_bin)
        title = meta.get("title", "YouTube Video")
        duration = float(meta.get("duration", 0.0) or 0.0)
        uploader = meta.get("uploader", "Unknown Uploader")
        raw_chapters = meta.get("chapters", []) or []

        # 2. Download subtitles
        sub_dir = work_dir / "subs"
        sub_file = download_subtitles(url, sub_dir, yt_dlp_bin=yt_dlp_bin)

        cues: List[Dict[str, Any]] = []
        full_transcript = ""

        if sub_file and sub_file.exists():
            content = sub_file.read_text(encoding="utf-8", errors="replace")
            raw_cues = parse_vtt_cues(content)
            cues = deduplicate_vtt_cues(raw_cues)
            full_transcript = clean_vtt_content(content)
            logger.info(
                f"[Ingestion: Fast Path] Subtitles acquired successfully for {url} "
                f"({len(cues)} cues, {len(full_transcript.split())} words). "
                f"Faster-Whisper audio transcription strictly skipped because official captions exist."
            )
        else:
            # 3. Fallback: ONLY when no subtitle tracks exist at all
            logger.info(f"No subtitle tracks found for {url}. Attempting whisper-cli fallback...")
            try:
                # Get direct audio stream URL with yt-dlp
                g_code, g_out, _ = run_cmd([yt_dlp_bin, "-g", "-f", "bestaudio", url], timeout=30)
                if g_code == 0 and g_out.strip():
                    stream_url = g_out.strip().splitlines()[0]
                    whisper_dir = work_dir / "whisper"
                    full_transcript = transcribe_audio_fallback(
                        stream_url,
                        whisper_dir,
                        ffmpeg_bin=ffmpeg_bin,
                        whisper_bin=whisper_bin,
                    )
                    # Check if generated .srt or .vtt file exists in whisper_dir
                    whisper_subs = (
                        sorted(whisper_dir.glob("*.srt")) + 
                        sorted(whisper_dir.glob("*.vtt"))
                    )
                    if whisper_subs:
                        w_content = whisper_subs[0].read_text(encoding="utf-8", errors="replace")
                        raw_cues = parse_vtt_cues(w_content)
                        cues = deduplicate_vtt_cues(raw_cues)
                        if not full_transcript:
                            full_transcript = clean_vtt_content(w_content)
            except Exception as e:
                logger.warning(f"Whisper fallback failed for {url}: {e}")

        # If transcript is still empty, synthesize from description
        if not full_transcript and meta.get("description"):
            full_transcript = meta["description"]

        # If cues are still empty but full_transcript and chapters exist, synthesize cues
        if not cues and full_transcript and raw_chapters:
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', full_transcript.strip()) if s.strip()]
            num_chaps = len(raw_chapters)
            if len(sentences) >= num_chaps:
                step = len(sentences) / num_chaps
                for idx, chap in enumerate(raw_chapters):
                    c_start = float(chap.get("start_time", 0.0))
                    c_end = float(chap.get("end_time", c_start + 60.0))
                    s_start_idx = int(idx * step)
                    s_end_idx = int((idx + 1) * step) if idx < num_chaps - 1 else len(sentences)
                    c_text = " ".join(sentences[s_start_idx:s_end_idx]).strip()
                    if c_text:
                        cues.append({"start": c_start, "end": c_end, "text": c_text})
            else:
                words = full_transcript.strip().split()
                step = len(words) / num_chaps
                for idx, chap in enumerate(raw_chapters):
                    c_start = float(chap.get("start_time", 0.0))
                    c_end = float(chap.get("end_time", c_start + 60.0))
                    w_start_idx = int(idx * step)
                    w_end_idx = int((idx + 1) * step) if idx < num_chaps - 1 else len(words)
                    c_text = " ".join(words[w_start_idx:w_end_idx]).strip()
                    if c_text:
                        cues.append({"start": c_start, "end": c_end, "text": c_text})

        # 4. Align cues to chapters
        chapters = align_cues_to_chapters(
            cues=cues,
            raw_chapters=raw_chapters,
            total_duration=duration,
            video_title=title,
        )

        # If chapters have empty text but full_transcript exists, populate chapters
        if chapters and not any(c.text.strip() for c in chapters) and full_transcript:
            if len(chapters) == 1:
                chapters[0].text = full_transcript
            else:
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', full_transcript.strip()) if s.strip()]
                num_chaps = len(chapters)
                if len(sentences) >= num_chaps:
                    step = len(sentences) / num_chaps
                    for idx, chap in enumerate(chapters):
                        s_start_idx = int(idx * step)
                        s_end_idx = int((idx + 1) * step) if idx < num_chaps - 1 else len(sentences)
                        chap.text = " ".join(sentences[s_start_idx:s_end_idx]).strip()
                else:
                    words = full_transcript.strip().split()
                    step = len(words) / num_chaps
                    for idx, chap in enumerate(chapters):
                        w_start_idx = int(idx * step)
                        w_end_idx = int((idx + 1) * step) if idx < num_chaps - 1 else len(words)
                        chap.text = " ".join(words[w_start_idx:w_end_idx]).strip()
                for chap in chapters:
                    if not chap.text.strip():
                        chap.text = full_transcript

        # 5. Download 720p video and extract high density frames if requested
        extracted_images: List[ExtractedImage] = []
        extracted_code_blocks: List[CodeBlock] = []

        if download_video:
            video_dir = work_dir / "video"
            logger.info(f"Downloading 720p stream for {url} (Duration: {duration:.1f}s)...")
            video_path = download_youtube_video_720p(url, video_dir, yt_dlp_bin=yt_dlp_bin)
            if video_path and video_path.exists():
                file_mb = video_path.stat().st_size / (1024 * 1024)
                logger.info(f"Video downloaded: {video_path.name} ({file_mb:.1f} MB). Extracting visual frames...")
                frames_dir = work_dir / "frames"
                frames = extract_high_density_frames(
                    video_path,
                    frames_dir,
                    duration_seconds=duration,
                    ffmpeg_bin=ffmpeg_bin,
                )
                # Invariant: AI Multimodal Visual Self-Analysis (Zero Programmatic Video OCR)
                # Never run programmatic OCR on video frames. All frames are cataloged directly
                # so the AI agent inspects them visually via its multimodal vision capabilities.
                for f_idx, f_path in enumerate(frames):
                    caption = f"Video frame {f_idx + 1} ({f_path.name})"
                    extracted_images.append(ExtractedImage(path=str(f_path), caption=caption, ocr_text=""))
                logger.info(f"Extracted {len(frames)} visual frames cataloged for AI multimodal visual self-analysis (zero OCR).")
            else:
                logger.warning(f"Video stream download did not produce a valid file for {url}. Visual frames skipped.")
        else:
            logger.info(f"[Ingestion: Fast Path] Video download skipped by policy (download_video=False).")

        # 6. Build IngestionSource
        source = IngestionSource(
            source_type="youtube",
            identifier=url,
            title=title,
            metadata={
                "video_id": extract_video_id(url) or meta.get("id", ""),
                "duration": duration,
                "uploader": uploader,
                "upload_date": meta.get("upload_date", ""),
                "view_count": meta.get("view_count", 0),
                "subtitles_extracted": bool(sub_file),
                "file_type": "youtube_stream",
            },
            chapters=chapters,
            extracted_code_blocks=extracted_code_blocks,
            extracted_images=extracted_images,
        )
        return source

    finally:
        if temp_dir_obj:
            temp_dir_obj.cleanup()


def ingest_youtube_url(
    url: str,
    output_dir: Optional[str | Path] = None,
    yt_dlp_bin: str = "yt-dlp",
    ffmpeg_bin: str = "ffmpeg",
    whisper_bin: str = "whisper-cli",
    download_video: bool = True,
) -> List[IngestionSource]:
    """Ingest a YouTube URL (either a single video or full playlist)."""
    if not is_youtube_url(url):
        raise ValueError(f"Invalid YouTube URL: {url}")

    if is_playlist_url(url):
        entries = extract_playlist_entries(url, yt_dlp_bin=yt_dlp_bin)
        sources: List[IngestionSource] = []
        for entry in entries:
            v_url = entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
            try:
                src = ingest_youtube_video(
                    v_url,
                    output_dir=output_dir,
                    yt_dlp_bin=yt_dlp_bin,
                    ffmpeg_bin=ffmpeg_bin,
                    whisper_bin=whisper_bin,
                    download_video=download_video,
                )
                sources.append(src)
            except Exception as e:
                logger.error(f"Failed to ingest playlist entry {v_url}: {e}")
        return sources
    else:
        return [
            ingest_youtube_video(
                url,
                output_dir=output_dir,
                yt_dlp_bin=yt_dlp_bin,
                ffmpeg_bin=ffmpeg_bin,
                whisper_bin=whisper_bin,
                download_video=download_video,
            )
        ]
