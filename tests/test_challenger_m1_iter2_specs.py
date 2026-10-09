"""Adversarial Challenge & Stress Suite for Iteration 2 User Specifications.

Authored by Milestone 1 Challenger (Iteration 2).
Empirically stress-tests the 3 new user specifications:
1. Mandatory 720p download arguments & subprocess handling.
2. Dynamic frame interval calculations across all duration boundaries & edge cases.
3. faster-whisper (large-v3-turbo) SRT timestamp formatting, parser roundtripping, and fallback cascades.
"""

from __future__ import annotations

import math
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, call, patch
import pytest

from scripts.ingestion import (
    calculate_dynamic_frame_interval,
    download_youtube_video_720p,
    extract_high_density_frames,
    format_srt_timestamp,
    ingest_youtube_url,
    ingest_youtube_video,
    parse_vtt_cues,
    transcribe_audio_faster_whisper,
)
from scripts.ingestion.yt_ingest import (
    format_seconds_timestamp,
    parse_timestamp_seconds,
    transcribe_audio_fallback,
)


# ===========================================================================
# 1. Mandatory 720p Download Specification Challenges
# ===========================================================================

class TestAdversarial720pDownload:
    """Adversarial challenges for yt-dlp 720p video download."""

    @patch("scripts.ingestion.yt_ingest.run_cmd")
    def test_720p_exact_format_specification_contract(self, mock_cmd):
        """CHALLENGE: Verify exact format string matches user requirement:
        -f "bestvideo[height<=720]+bestaudio/best[height<=720]"
        """
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            mock_vid = out_dir / "vid_xyz.mp4"
            mock_vid.touch()
            mock_cmd.return_value = (0, "Success", "")

            target_url = "https://www.youtube.com/watch?v=vid_xyz"
            res = download_youtube_video_720p(target_url, out_dir)
            assert res == mock_vid

            args = mock_cmd.call_args[0][0]
            assert "-f" in args
            fmt_idx = args.index("-f")
            exact_fmt = args[fmt_idx + 1]
            assert exact_fmt == "bestvideo[height<=720]+bestaudio/best[height<=720]", (
                f"Format specifier mismatch: got '{exact_fmt}'"
            )
            assert "--no-playlist" in args, "Must specify --no-playlist for single video 720p downloads"

    @patch("scripts.ingestion.yt_ingest.run_cmd")
    def test_720p_download_handles_various_container_extensions(self, mock_cmd):
        """CHALLENGE: yt-dlp may merge streams into .mkv, .webm, or .m4v depending on codecs."""
        for ext in [".mp4", ".mkv", ".webm", ".m4v"]:
            with tempfile.TemporaryDirectory() as td:
                out_dir = Path(td)
                downloaded_file = out_dir / f"test_vid{ext}"
                downloaded_file.touch()
                mock_cmd.return_value = (0, "OK", "")

                result = download_youtube_video_720p("https://www.youtube.com/watch?v=test_vid", out_dir)
                assert result is not None, f"Failed to detect video with extension {ext}"
                assert result.suffix == ext

    @patch("scripts.ingestion.yt_ingest.run_cmd")
    def test_720p_download_failure_with_clean_directory_returns_none(self, mock_cmd):
        """CHALLENGE: Command failure (code != 0) without any created file returns None."""
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            mock_cmd.return_value = (1, "", "ERROR: Video unavailable in 720p")

            res = download_youtube_video_720p("https://www.youtube.com/watch?v=unavailable", out_dir)
            assert res is None

    @patch("scripts.ingestion.yt_ingest.run_cmd")
    def test_720p_download_fails_when_stale_file_present(self, mock_cmd):
        """CHALLENGE: If yt-dlp fails (code != 0), must NOT return a pre-existing stale video file!"""
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            stale_vid = out_dir / "stale_unrelated_video.mp4"
            stale_vid.touch()
            mock_cmd.return_value = (1, "", "ERROR: Download failed")

            res = download_youtube_video_720p("https://www.youtube.com/watch?v=target_vid", out_dir)
            # If download failed, returning stale_vid is a false positive
            assert res is None, f"Returned stale video {res} despite yt-dlp failure"

    @patch("scripts.ingestion.yt_ingest.run_cmd")
    def test_720p_download_multiple_videos_in_dir_returns_target_video(self, mock_cmd):
        """CHALLENGE: When downloading into a directory with prior videos, must return target video ID file!"""
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            prior_vid = out_dir / "aaa_prior_video.mp4"
            prior_vid.touch()
            target_vid = out_dir / "zzz_target_id.mp4"
            target_vid.touch()
            mock_cmd.return_value = (0, "Downloaded", "")

            target_url = "https://www.youtube.com/watch?v=zzz_target_id"
            res = download_youtube_video_720p(target_url, out_dir)
            assert res == target_vid, (
                f"Expected target video {target_vid.name}, but got prior video {res.name if res else None}"
            )

    @patch("scripts.ingestion.yt_ingest.extract_playlist_entries")
    @patch("scripts.ingestion.yt_ingest.ingest_youtube_video")
    def test_playlist_ingestion_propagates_download_video_flag(
        self, mock_ingest_vid, mock_extract_entries
    ):
        """CHALLENGE: When ingesting a playlist with download_video=True,
        every playlist item must be passed download_video=True.
        """
        mock_extract_entries.return_value = [
            {"id": "vid1", "url": "https://www.youtube.com/watch?v=vid1"},
            {"id": "vid2", "url": "https://www.youtube.com/watch?v=vid2"},
        ]
        mock_ingest_vid.return_value = MagicMock()

        playlist_url = "https://www.youtube.com/playlist?list=PL_TEST_PLAYLIST"
        sources = ingest_youtube_url(playlist_url, download_video=True)
        assert len(sources) == 2
        assert mock_ingest_vid.call_count == 2
        for call_item in mock_ingest_vid.call_args_list:
            assert call_item.kwargs.get("download_video") is True


# ===========================================================================
# 2. Dynamic Frame Interval Calculation Edge Duration Challenges
# ===========================================================================

class TestAdversarialDynamicFrameInterval:
    """Adversarial challenges for dynamic frame interval calculation across edge durations."""

    def test_exact_interval_tier_boundaries(self):
        """CHALLENGE: Test strictly on and across tier boundaries:
        - Tier 1: <= 120s  -> 1.0s (1.0 fps)
        - Tier 2: 120-600s -> 2.0s (0.5 fps)
        - Tier 3: 600-1800s -> 5.0s (0.2 fps)
        - Tier 4: 1800-3600s -> 10.0s (0.1 fps)
        - Tier 5: > 3600s   -> 20.0s (0.05 fps)
        """
        # Tier 1 boundaries
        assert calculate_dynamic_frame_interval(0.0) == 1.0
        assert calculate_dynamic_frame_interval(1.0) == 1.0
        assert calculate_dynamic_frame_interval(60.0) == 1.0
        assert calculate_dynamic_frame_interval(119.999) == 1.0
        assert calculate_dynamic_frame_interval(120.0) == 1.0

        # Tier 2 boundaries
        assert calculate_dynamic_frame_interval(120.0001) == 2.0
        assert calculate_dynamic_frame_interval(121.0) == 2.0
        assert calculate_dynamic_frame_interval(300.0) == 2.0
        assert calculate_dynamic_frame_interval(599.999) == 2.0
        assert calculate_dynamic_frame_interval(600.0) == 2.0

        # Tier 3 boundaries
        assert calculate_dynamic_frame_interval(600.0001) == 5.0
        assert calculate_dynamic_frame_interval(601.0) == 5.0
        assert calculate_dynamic_frame_interval(1200.0) == 5.0
        assert calculate_dynamic_frame_interval(1799.999) == 5.0
        assert calculate_dynamic_frame_interval(1800.0) == 5.0

        # Tier 4 boundaries
        assert calculate_dynamic_frame_interval(1800.0001) == 10.0
        assert calculate_dynamic_frame_interval(1801.0) == 10.0
        assert calculate_dynamic_frame_interval(2700.0) == 10.0
        assert calculate_dynamic_frame_interval(3599.999) == 10.0
        assert calculate_dynamic_frame_interval(3600.0) == 10.0

        # Tier 5 boundaries
        assert calculate_dynamic_frame_interval(3600.0001) == 20.0
        assert calculate_dynamic_frame_interval(3601.0) == 20.0
        assert calculate_dynamic_frame_interval(7200.0) == 20.0
        assert calculate_dynamic_frame_interval(86400.0) == 20.0
        assert calculate_dynamic_frame_interval(1_000_000.0) == 20.0

    def test_negative_and_zero_duration_robustness(self):
        """CHALLENGE: Pathological or malformed durations (negative, zero) must clamp safely."""
        assert calculate_dynamic_frame_interval(-0.0) == 1.0
        assert calculate_dynamic_frame_interval(-50.0) == 1.0
        assert calculate_dynamic_frame_interval(-1e9) == 1.0

    def test_dynamic_frame_rate_yields_practical_frame_counts(self):
        """ORACLE: Over any practical duration, frame count must be bounded and high-density.
        - For 2-min video: ~120 frames (captures rapid slide transitions)
        - For 10-min video: ~300 frames
        - For 30-min video: ~360 frames
        - For 1-hour video: ~360 frames
        - For 3-hour video: ~540 frames
        """
        duration_cases = [120.0, 600.0, 1800.0, 3600.0, 10800.0]
        for dur in duration_cases:
            interval = calculate_dynamic_frame_interval(dur)
            fps = 1.0 / interval
            estimated_frames = dur * fps
            assert estimated_frames >= 100, f"Frame density too low for duration {dur}: {estimated_frames}"
            assert estimated_frames <= 1000, f"Frame count excessively high for duration {dur}: {estimated_frames}"

    @patch("scripts.ingestion.yt_ingest.run_cmd")
    def test_extract_high_density_frames_filter_construction(self, mock_cmd):
        """CHALLENGE: Verify ffmpeg command construction for high density extraction."""
        with tempfile.TemporaryDirectory() as td:
            dummy_vid = Path(td) / "lecture.mp4"
            dummy_vid.touch()
            frames_dir = Path(td) / "frames"
            mock_cmd.return_value = (0, "", "")

            # 1. Short video (60s) -> interval = 1.0 -> fps = 1.0000
            extract_high_density_frames(dummy_vid, frames_dir, duration_seconds=60.0)
            args1 = mock_cmd.call_args[0][0]
            assert "fps=1.0000" in args1[args1.index("-vf") + 1]
            assert args1[args1.index("-q:v") + 1] == "2"

            # 2. Long video (7200s) -> interval = 20.0 -> fps = 0.0500
            extract_high_density_frames(dummy_vid, frames_dir, duration_seconds=7200.0)
            args2 = mock_cmd.call_args[0][0]
            assert "fps=0.0500" in args2[args2.index("-vf") + 1]


# ===========================================================================
# 3. faster-whisper (large-v3-turbo) SRT Formatting & Fallback Challenges
# ===========================================================================

class TestAdversarialFasterWhisperSRT:
    """Adversarial challenges for faster-whisper SRT formatting and fallback."""

    def test_format_srt_timestamp_exhaustive_oracle(self):
        r"""ORACLE: Verify strict standard SRT timestamp regex: ^\d{2,}:\d{2}:\d{2},\d{3}$
        and mathematical exactness.
        """
        srt_regex = re.compile(r"^\d{2,}:\d{2}:\d{2},\d{3}$")

        test_points = [
            (0.0, "00:00:00,000"),
            (0.001, "00:00:00,001"),
            (0.5, "00:00:00,500"),
            (0.999, "00:00:00,999"),
            (1.0, "00:00:01,000"),
            (59.0, "00:00:59,000"),
            (59.999, "00:00:59,999"),
            (60.0, "00:01:00,000"),
            (61.5, "00:01:01,500"),
            (3599.999, "00:59:59,999"),
            (3600.0, "01:00:00,000"),
            (3661.123, "01:01:01,123"),
            (86399.999, "23:59:59,999"),
            (86400.0, "24:00:00,000"),
            (90061.050, "25:01:01,050"),
        ]

        for sec, expected in test_points:
            formatted = format_srt_timestamp(sec)
            assert formatted == expected, f"Failed on {sec}: expected '{expected}', got '{formatted}'"
            assert srt_regex.match(formatted), f"Timestamp '{formatted}' violates standard SRT syntax"

    def test_format_srt_timestamp_negative_and_rounding_edge_cases(self):
        """CHALLENGE: Millisecond rounding boundary cases (e.g. 59.9999s)."""
        # Negative seconds should clamp safely to 00:00:00,000
        assert format_srt_timestamp(-10.0) == "00:00:00,000"

        # 0.9999s should round/clamp to 999ms rather than 1000ms
        res = format_srt_timestamp(0.9999)
        assert res == "00:00:00,999"

        # 59.9999s should round/clamp to 999ms rather than invalid 00:00:59,1000
        res_59 = format_srt_timestamp(59.9999)
        assert res_59 == "00:00:59,999"

    def test_faster_whisper_generates_standard_conforming_srt(self):
        """CHALLENGE: Verify generated .srt file contains correct cue indices,
        standard ' --> ' separators, blank line delimiters, and verbatim text.
        """
        with tempfile.TemporaryDirectory() as td:
            audio_path = Path(td) / "deep_dive.wav"
            audio_path.touch()
            out_dir = Path(td) / "srt_out"

            mock_segments = [
                MagicMock(start=1.2, end=4.5, text="First utterance on event loop."),
                MagicMock(start=5.0, end=8.75, text="Second utterance: microtask queue."),
                MagicMock(start=9.0, end=15.123, text="Third utterance with code `queueMicrotask()`."),
            ]
            mock_model = MagicMock()
            mock_model.transcribe.return_value = (mock_segments, {})

            with patch("faster_whisper.WhisperModel", return_value=mock_model):
                srt_path, transcript = transcribe_audio_faster_whisper(
                    audio_path,
                    out_dir,
                    model_size="large-v3-turbo",
                )

                assert srt_path is not None
                assert srt_path.exists()
                raw_srt = srt_path.read_text(encoding="utf-8")

                # Verify each cue block format
                expected_blocks = [
                    "1\n00:00:01,200 --> 00:00:04,500\nFirst utterance on event loop.",
                    "2\n00:00:05,000 --> 00:00:08,750\nSecond utterance: microtask queue.",
                    "3\n00:00:09,000 --> 00:00:15,123\nThird utterance with code `queueMicrotask()`.",
                ]
                for block in expected_blocks:
                    assert block in raw_srt, f"Expected block not found in SRT:\n{block}\n\nFull SRT:\n{raw_srt}"

                # Verify cues can be parsed back by parse_vtt_cues
                cues = parse_vtt_cues(raw_srt)
                assert len(cues) == 3
                assert cues[0]["start"] == 1.2
                assert cues[0]["end"] == 4.5
                assert cues[0]["text"] == "First utterance on event loop."
                assert cues[1]["start"] == 5.0
                assert cues[1]["end"] == 8.75
                assert cues[2]["start"] == 9.0
                assert cues[2]["end"] == 15.123

    @patch("scripts.ingestion.yt_ingest.run_cmd")
    def test_transcribe_audio_fallback_cascade_to_whisper_cli_when_faster_whisper_fails(
        self, mock_cmd
    ):
        """CHALLENGE: Cascade resilience:
        When faster-whisper raises an exception (e.g. GPU OOM or missing dependency),
        transcribe_audio_fallback MUST gracefully fall back to whisper-cli Metal GPU.
        """
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            dummy_media = "https://audio.stream/test.m3u8"

            def fake_run_cmd(args, timeout=180):
                if "-ar" in args:
                    # ffmpeg wav conversion
                    wav_file = Path(args[-1])
                    wav_file.touch()
                    return (0, "", "")
                elif "whisper-cli" in args[0]:
                    # whisper-cli execution
                    out_vtt = out_dir / "whisper_transcript.vtt"
                    out_vtt.write_text(
                        "WEBVTT\n\n00:00:01.000 --> 00:00:05.000\nWhisper-cli Metal fallback text.\n",
                        encoding="utf-8",
                    )
                    return (0, "Done", "")
                return (0, "", "")

            mock_cmd.side_effect = fake_run_cmd

            with patch(
                "faster_whisper.WhisperModel",
                side_effect=RuntimeError("CUDA Out of Memory in large-v3-turbo"),
            ):
                text = transcribe_audio_fallback(dummy_media, out_dir)
                assert "Whisper-cli Metal fallback text" in text

    @patch("scripts.ingestion.yt_ingest.extract_video_metadata")
    @patch("scripts.ingestion.yt_ingest.download_subtitles")
    @patch("scripts.ingestion.yt_ingest.run_cmd")
    @patch("scripts.ingestion.yt_ingest.transcribe_audio_fallback")
    def test_whisper_fallback_in_ingest_youtube_video_leaves_subsequent_chapters_empty(
        self, mock_fallback, mock_run_cmd, mock_subs, mock_meta
    ):
        """CHALLENGE: When subtitles are missing, whisper generates an SRT,
        but ingest_youtube_video does not populate cues from the SRT, causing all
        chapters after chapter 1 to have completely empty text!
        """
        mock_meta.return_value = {
            "id": "chap_vid",
            "title": "Two Chapter Lecture",
            "duration": 200.0,
            "uploader": "Tester",
            "chapters": [
                {"title": "Introduction", "start_time": 0.0, "end_time": 100.0},
                {"title": "Advanced Topics", "start_time": 100.0, "end_time": 200.0},
            ],
        }
        mock_subs.return_value = None  # No subtitles available
        mock_run_cmd.return_value = (0, "https://audio.stream/url\n", "")
        mock_fallback.return_value = "Part 1 text. Part 2 text."

        source = ingest_youtube_video(
            "https://www.youtube.com/watch?v=chap_vid",
            download_video=False,
        )

        assert len(source.chapters) == 2
        # Observe what happens to chapter 2 text:
        assert source.chapters[1].text != "", (
            f"Defect: Chapter 2 text is empty because cues were not extracted from whisper transcript!"
        )
