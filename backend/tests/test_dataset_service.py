"""
Tests for dataset service utilities.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.utils.file_utils import (
    count_files,
    get_directory_info,
    list_image_files,
    ensure_directory,
)


@pytest.fixture()
def sample_dir():
    """Create a temporary directory with sample files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample image files
        for i in range(5):
            (Path(tmpdir) / f"image_{i}.jpg").touch()

        # Create a non-image file
        (Path(tmpdir) / "data.csv").write_text("col1,col2\n1,2\n3,4")

        # Create a subdirectory with more images
        sub = Path(tmpdir) / "subdir"
        sub.mkdir()
        for i in range(3):
            (sub / f"sub_image_{i}.png").touch()

        yield tmpdir


def test_list_image_files(sample_dir):
    """Should find all image files recursively."""
    images = list_image_files(sample_dir)
    assert len(images) == 8  # 5 jpg + 3 png


def test_count_files_all(sample_dir):
    """Should count all files."""
    total = count_files(sample_dir)
    assert total == 9  # 8 images + 1 csv


def test_count_files_with_filter(sample_dir):
    """Should count only .jpg files."""
    count = count_files(sample_dir, extensions={".jpg"})
    assert count == 5


def test_get_directory_info(sample_dir):
    """Should return summary info."""
    info = get_directory_info(sample_dir)
    assert info["exists"] is True
    assert info["total_files"] == 9
    assert ".jpg" in info["extensions"]
    assert ".csv" in info["extensions"]


def test_get_directory_info_missing():
    """Should handle non-existent directories."""
    info = get_directory_info("/nonexistent/path/xyz")
    assert info["exists"] is False


def test_ensure_directory():
    """Should create directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        new_dir = Path(tmpdir) / "a" / "b" / "c"
        result = ensure_directory(new_dir)
        assert result.exists()
        assert result.is_dir()
