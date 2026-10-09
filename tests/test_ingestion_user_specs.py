"""Verification test suite for user specifications (Iteration 2).

Tests:
1. Mandatory 720p YouTube Video Download (-f "bestvideo[height<=720]+bestaudio/best[height<=720]").
2. Dynamic High-Density Frame Extraction & Analysis based on video duration.
3. faster-whisper (large-v3-turbo) audio fallback generating timestamped .srt files.
4. End-to-end integration in ingest_youtube_video.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from scripts.ingestion import (
    calculate_dynamic_frame_interval,
    download_youtube_video_720p,
    extract_high_density_frames,
    format_srt_timestamp,
    ingest_youtube_video,
    transcribe_audio_faster_whisper,
)
from scripts.ingestion.yt_ingest import transcribe_audio_fallback


class TestMandatory720pDownload:
    """Tests for mandatory 720p video download specification."""

    @patch("scripts.ingestion.yt_ingest.run_cmd")
    def test_720p_video_download_format_arguments(self, mock_cmd):
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            mock_vid = out_dir / "vid123.mp4"
            mock_vid.touch()
            mock_cmd.return_value = (0, "Downloaded", "")

            result = download_youtube_video_720p("https://www.youtube.com/watch?v=vid123", out_dir)
            assert result == mock_vid
            assert mock_cmd.called
            args = mock_cmd.call_args[0][0]
            assert "-f" in args
            idx = args.index("-f")
            assert args[idx + 1] == "bestvideo[height<=720]+bestaudio/best[height<=720]"
            assert "--no-playlist" in args
            assert "https://www.youtube.com/watch?v=vid123" in args

    @patch("scripts.ingestion.yt_ingest.run_cmd")
    def test_720p_video_download_failure_returns_none(self, mock_cmd):
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            mock_cmd.return_value = (1, "", "Network error")

            result = download_youtube_video_720p("https://www.youtube.com/watch?v=vid123", out_dir)
            assert result is None


class TestDynamicFrameExtraction:
    """Tests for dynamic high-density frame extraction."""

    def test_dynamic_frame_interval_density_thresholds(self):
        # <= 2 mins (120s): 1.0s interval (1.0 fps)
        assert calculate_dynamic_frame_interval(30.0) == 1.0
        assert calculate_dynamic_frame_interval(120.0) == 1.0

        # 2-10 mins (600s): 2.0s interval (0.5 fps)
        assert calculate_dynamic_frame_interval(121.0) == 2.0
        assert calculate_dynamic_frame_interval(600.0) == 2.0

        # 10-30 mins (1800s): 5.0s interval (0.2 fps)
        assert calculate_dynamic_frame_interval(601.0) == 5.0
        assert calculate_dynamic_frame_interval(1800.0) == 5.0

        # 30-60 mins (3600s): 10.0s interval (0.1 fps)
        assert calculate_dynamic_frame_interval(1801.0) == 10.0
        assert calculate_dynamic_frame_interval(3600.0) == 10.0

        # > 60 mins: 20.0s interval (0.05 fps)
        assert calculate_dynamic_frame_interval(3601.0) == 20.0
        assert calculate_dynamic_frame_interval(7200.0) == 20.0

    @patch("scripts.ingestion.yt_ingest.run_cmd")
    def test_extract_high_density_frames_ffmpeg_arguments(self, mock_cmd):
        with tempfile.TemporaryDirectory() as td:
            dummy_vid = Path(td) / "test.mp4"
            dummy_vid.touch()
            frames_dir = Path(td) / "frames"

            def fake_ffmpeg(args, timeout=300):
                # Simulate ffmpeg generating 3 frames
                frames_dir.mkdir(parents=True, exist_ok=True)
                (frames_dir / "frame_0001.jpg").touch()
                (frames_dir / "frame_0002.jpg").touch()
                (frames_dir / "frame_0003.jpg").touch()
                return (0, "", "")

            mock_cmd.side_effect = fake_ffmpeg

            frames = extract_high_density_frames(dummy_vid, frames_dir, duration_seconds=120.0)
            assert len(frames) == 3
            assert all(f.suffix == ".jpg" for f in frames)

            assert mock_cmd.called
            args = mock_cmd.call_args[0][0]
            assert "-vf" in args
            vf_idx = args.index("-vf")
            assert "fps=1.0000" in args[vf_idx + 1]
            assert "-q:v" in args
            assert args[args.index("-q:v") + 1] == "2"


class TestFasterWhisperSRTTranscription:
    """Tests for faster-whisper (large-v3-turbo) timestamped .srt output."""

    def test_format_srt_timestamp(self):
        assert format_srt_timestamp(0.0) == "00:00:00,000"
        assert format_srt_timestamp(0.5) == "00:00:00,500"
        assert format_srt_timestamp(65.123) == "00:01:05,123"
        assert format_srt_timestamp(3661.005) == "01:01:01,005"
        assert format_srt_timestamp(7322.999) == "02:02:02,999"

    def test_transcribe_audio_faster_whisper_generates_valid_srt(self):
        with tempfile.TemporaryDirectory() as td:
            audio_path = Path(td) / "lecture.wav"
            audio_path.touch()
            out_dir = Path(td) / "output"

            # Mock faster_whisper.WhisperModel
            mock_segment_1 = MagicMock(start=0.0, end=2.5, text="Welcome to the lecture.")
            mock_segment_2 = MagicMock(start=2.5, end=5.8, text="Today we discuss Node.js internals.")

            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([mock_segment_1, mock_segment_2], {})

            with patch("faster_whisper.WhisperModel", return_value=mock_model):
                srt_path, transcript = transcribe_audio_faster_whisper(
                    audio_path,
                    out_dir,
                    model_size="large-v3-turbo",
                )

                assert srt_path is not None
                assert srt_path.exists()
                assert srt_path.suffix == ".srt"

                srt_content = srt_path.read_text(encoding="utf-8")
                # Validate standard SRT format
                assert "1\n00:00:00,000 --> 00:00:02,500\nWelcome to the lecture." in srt_content
                assert "2\n00:00:02,500 --> 00:00:05,800\nToday we discuss Node.js internals." in srt_content

                assert "Welcome to the lecture. Today we discuss Node.js internals." == transcript

    @patch("scripts.ingestion.yt_ingest.run_cmd")
    @patch("scripts.ingestion.yt_ingest.transcribe_audio_faster_whisper")
    def test_transcribe_audio_fallback_pipeline(self, mock_fw, mock_cmd):
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)

            def fake_ffmpeg(args, timeout=180):
                # Create fake wav file when ffmpeg is run
                wav_target = Path(args[-1])
                wav_target.touch()
                return (0, "", "")

            mock_cmd.side_effect = fake_ffmpeg
            mock_srt = out_dir / "temp_audio_16k_transcript.srt"
            mock_srt.touch()
            mock_fw.return_value = (mock_srt, "Transcribed via faster-whisper large-v3-turbo")

            text = transcribe_audio_fallback("https://stream.audio/test.m3u8", out_dir)
            assert text == "Transcribed via faster-whisper large-v3-turbo"
            assert mock_fw.called


class TestIntegrationYouTubeIngestionWithSpecs:
    """Tests for integration of 720p and frame extraction in ingest_youtube_video."""

    @patch("scripts.ingestion.yt_ingest.extract_video_metadata")
    @patch("scripts.ingestion.yt_ingest.download_subtitles")
    @patch("scripts.ingestion.yt_ingest.download_youtube_video_720p")
    @patch("scripts.ingestion.yt_ingest.extract_high_density_frames")
    @patch("scripts.ingestion.file_extract.perform_apple_vision_ocr")
    def test_ingest_youtube_video_with_frame_extraction(
        self,
        mock_ocr,
        mock_extract_frames,
        mock_dl_720p,
        mock_subs,
        mock_meta,
    ):
        mock_meta.return_value = {
            "id": "vid789",
            "title": "Architecture Masterclass",
            "duration": 300,
            "uploader": "Sparsh",
            "chapters": [],
        }

        with tempfile.TemporaryDirectory() as td:
            sub_file = Path(td) / "vid789.en.vtt"
            sub_file.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:05.000\nSystem architecture intro.\n")
            mock_subs.return_value = sub_file

            fake_vid = Path(td) / "vid789.mp4"
            fake_vid.touch()
            mock_dl_720p.return_value = fake_vid

            frame1 = Path(td) / "frame_0001.jpg"
            frame1.touch()
            mock_extract_frames.return_value = [frame1]
            mock_ocr.return_value = "function connect() {\n  return db;\n}"

            source = ingest_youtube_video(
                "https://www.youtube.com/watch?v=vid789",
                output_dir=td,
                download_video=True,
            )

            assert source.source_type == "youtube"
            assert len(source.extracted_images) >= 1
            assert source.extracted_images[0].path == str(frame1)
            assert "function connect" in source.extracted_images[0].ocr_text
            assert len(source.extracted_code_blocks) >= 1
            assert source.extracted_code_blocks[0].code == "function connect() {\n  return db;\n}"
