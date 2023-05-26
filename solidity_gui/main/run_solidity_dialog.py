"""This module provides functionality to run Solidity."""
from pathlib import Path

from PySide6.QtWidgets import QFileDialog

from solidity_gui.solidity import run_solidity


def get_file_paths() -> list[str]:
    """Get the file paths from the user."""
    file_paths = []
    file_names = ["BST.Y3D", "layout.txt", "pellet.txt", "mat.txt"]
    for i in range(4):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setWindowTitle("Select " + file_names[i])
        file_dialog.exec_()
        file_paths.append(file_dialog.selectedFiles()[0])
    return file_paths


def run_solidity_dialog() -> None:
    """Run Solidity with the file paths selected by the user."""
    file_paths = get_file_paths()
    run_solidity(
        Path(file_paths[0]),
        Path(file_paths[1]),
        Path(file_paths[2]),
        Path(file_paths[3]),
    )
