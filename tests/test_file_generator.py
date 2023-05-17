"""Tests for solidity_gui.main.solidity_file_generator module."""

import tempfile
from solidity_gui.main.solidity_file_generator import write_file


def test_write_file():
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        # Write some test data to the file
        file_content = "Hello, world!"
        write_file(file_content, f.name)

    # Read the contents of the file and check that they match the expected value
    with open(f.name, "r") as f:
        assert f.read() == file_content
