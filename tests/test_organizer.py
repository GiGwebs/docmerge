"""Basic tests for DocMerge."""

import pytest
from pathlib import Path
import tempfile
import os

from docmerge.organizer import DocumentOrganizer
from docmerge.converter import is_supported_file, get_file_type, extract_sort_key


class TestConverter:
    """Tests for converter utilities."""

    def test_is_supported_file_pdf(self):
        assert is_supported_file("test.pdf") is True

    def test_is_supported_file_docx(self):
        assert is_supported_file("test.docx") is True

    def test_is_supported_file_images(self):
        assert is_supported_file("test.jpg") is True
        assert is_supported_file("test.png") is True
        assert is_supported_file("test.gif") is True

    def test_is_supported_file_unsupported(self):
        assert is_supported_file("test.txt") is False
        assert is_supported_file("test.exe") is False

    def test_get_file_type(self):
        assert get_file_type("test.pdf") == "pdf"
        assert get_file_type("test.docx") == "docx"
        assert get_file_type("test.jpg") == "image"
        assert get_file_type("test.txt") == "unknown"


class TestOrganizer:
    """Tests for DocumentOrganizer."""

    def test_extract_sort_key(self):
        organizer = DocumentOrganizer("/tmp", "/tmp/out", verbose=False)
        
        # Test numbered files
        assert organizer.extract_sort_key("1) File.pdf")[0] == 1
        assert organizer.extract_sort_key("2. File.pdf")[0] == 2
        assert organizer.extract_sort_key("10-File.pdf")[0] == 10
        
        # Test unnumbered files
        assert organizer.extract_sort_key("File.pdf")[0] == 999

    def test_is_system_file(self):
        organizer = DocumentOrganizer("/tmp", "/tmp/out", verbose=False)
        
        assert organizer.is_system_file(".DS_Store") is True
        assert organizer.is_system_file("desktop.ini") is True
        assert organizer.is_system_file("Thumbs.db") is True
        assert organizer.is_system_file("document.pdf") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
