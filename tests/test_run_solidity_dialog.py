from unittest.mock import patch
from PySide6.QtWidgets import QFileDialog
from solidity_gui.main.run_solidity_dialog import get_file_paths, run_solidity_dialog


@patch.object(QFileDialog, "exec_", return_value=True)
def test_get_file_paths(mock_exec):
    # Test that the function returns a list of file paths
    expected_file_paths = [
        "/path/to/BST.Y3D",
        "/path/to/layout.txt",
        "/path/to/pellet.txt",
        "/path/to/mat.txt",
    ]
    with patch.object(QFileDialog, "selectedFiles", return_value=expected_file_paths):
        file_paths = get_file_paths()
        assert file_paths == expected_file_paths


@patch("solidity_gui.main.run_solidity")
@patch("solidity_gui.main.run_solidity_dialog.get_file_paths")
def test_run_solidity_dialog(mock_get_file_paths, mock_run_solidity):
    # Test that the function calls get_file_paths and run_solidity with the correct arguments
    expected_file_paths = [
        "/path/to/BST.Y3D",
        "/path/to/layout.txt",
        "/path/to/pellet.txt",
        "/path/to/mat.txt",
    ]
    mock_get_file_paths.return_value = expected_file_paths
    run_solidity_dialog()
    mock_get_file_paths.assert_called_once()
    mock_run_solidity.assert_called_once_with(*expected_file_paths)
