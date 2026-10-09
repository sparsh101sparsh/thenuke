"""Shared fixtures and configuration for thenuke test suite."""

import os
import re
import json
import shutil
import tempfile
import importlib
from pathlib import Path
import pytest

# Constants from PROJECT.md & ORIGINAL_REQUEST.md
DEVANAGARI_REGEX = re.compile(r'[\u0900-\u097F\uA8E0-\uA8FF\u1CD0-\u1CFF]')
MONOCHROME_PALETTE = {
    '#000000', '#222222', '#444444', '#CCCCCC', '#F1F5F9', '#F8F8F8', '#FFFFFF'
}
BRANDING_AUTHORS = "@issparsh @sumitsingh097"
ISO_A4_WIDTH = 595.28
ISO_A4_HEIGHT = 841.89
PAGE_MARGIN_MIN = 54.0


@pytest.fixture(scope="session")
def fixtures_dir():
    """Returns absolute path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_vtt_path(fixtures_dir):
    """Path to sample WebVTT subtitle fixture."""
    return fixtures_dir / "sample_vtt.vtt"


@pytest.fixture(scope="session")
def sample_slides_path(fixtures_dir):
    """Path to sample PPTX slides fixture."""
    return fixtures_dir / "sample_slides.pptx"


@pytest.fixture(scope="session")
def sample_doc_path(fixtures_dir):
    """Path to sample PDF document fixture."""
    return fixtures_dir / "sample_doc.pdf"


@pytest.fixture(scope="session")
def test_corpus_path(fixtures_dir):
    """Path to pre-built test corpus fixture."""
    return fixtures_dir / "test_corpus.json"


@pytest.fixture(scope="session")
def sample_grilling_profile_path(fixtures_dir):
    """Path to sample grilling profile fixture."""
    return fixtures_dir / "sample_grilling_profile.json"


@pytest.fixture(scope="session")
def sample_dom_path(fixtures_dir):
    """Path to sample DOM HTML capture fixture."""
    return fixtures_dir / "sample_dom.html"


@pytest.fixture(scope="session")
def sample_manual_dir(fixtures_dir):
    """Path to sample synthesized manual directory."""
    return fixtures_dir / "sample_synthesized_manual"


@pytest.fixture
def temp_workspace():
    """Provides an isolated temporary directory for test executions and cleans it up."""
    temp_dir = tempfile.mkdtemp(prefix="nuke_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


def safe_load_module(module_name: str):
    """Safely import a module from scripts, returning None if not yet implemented."""
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        return None
    except Exception:
        raise
