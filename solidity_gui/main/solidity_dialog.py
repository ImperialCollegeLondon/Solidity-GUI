"""This module provides functionality to run Solidity."""
from pathlib import Path

from pubsub import pub
from PySide6.QtWidgets import QFileDialog


def get_file_paths() -> list[str] | None:
    """Get the file paths from the user."""
    file_paths = []
    file_names = ["BST.Y3D", "layout.txt", "pellet.txt", "mat.txt"]
    for i in range(4):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setWindowTitle("Select " + file_names[i])
        if file_dialog.exec_() == QFileDialog.DialogCode.Rejected:
            return None
        file_paths.append(file_dialog.selectedFiles()[0])
    return file_paths


def run_solidity() -> None:
    """Run Solidity with the file paths selected by the user."""
    if file_paths := get_file_paths():
        pub.sendMessage(
            "docker.start",
            y3d_file_path=Path(file_paths[0]),
            layout_file_path=Path(file_paths[1]),
            pellet_file_path=Path(file_paths[2]),
            materials_file_path=Path(file_paths[3]),
        )
