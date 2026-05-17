"""Shared fixtures for Yokino tests."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure yokino package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir():
    """Temporary directory that auto-cleans up."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def mock_config():
    """Mock get_config with sensible defaults for testing."""
    with patch("yokino.config._config", None):
        from yokino.config import Config, get_config

        yield get_config()


@pytest.fixture
def sample_reminders_file(tmp_path):
    """Create a sample reminders.json and patch the path."""
    from yokino.core.tools import reminder as rmod

    orig = rmod.REMINDERS_FILE
    p = tmp_path / "reminders.json"
    p.write_text("[]", encoding="utf-8")
    rmod.REMINDERS_FILE = p
    yield p
    rmod.REMINDERS_FILE = orig


@pytest.fixture
def sample_notes_dir(tmp_path):
    """Create a temp notes dir and patch the path."""
    from yokino.core.tools import note as nmod

    orig = nmod.NOTES_DIR
    d = tmp_path / "notes"
    d.mkdir(parents=True, exist_ok=True)
    nmod.NOTES_DIR = d
    yield d
    nmod.NOTES_DIR = orig


@pytest.fixture
def sample_knowledge_dir(tmp_path):
    """Create a temp knowledge dir and patch KnowledgeBase to use it."""
    d = tmp_path / "test_knowledge"
    d.mkdir(parents=True, exist_ok=True)
    for sub in ("notes", "bookmarks", "reference"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    yield d


@pytest.fixture
def sample_workflows_dir(tmp_path):
    """Create a temp workflows dir and patch the path."""
    from yokino.core.tools import workflow as wmod

    orig = wmod.WORKFLOWS_DIR
    d = tmp_path / "workflows"
    d.mkdir(parents=True, exist_ok=True)
    wmod.WORKFLOWS_DIR = d
    yield d
    wmod.WORKFLOWS_DIR = orig
