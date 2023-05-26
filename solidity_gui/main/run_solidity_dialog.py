"""This module provides functionality to run Solidity."""
from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QMessageBox
from solidity_gui.solidity import run_solidity


def run_solidity_dialog():
    file_paths = []
    file_names = ["BST.Y3D", "layout.txt", "pellet.txt", "mat.txt"]
    for i in range(4):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setWindowTitle("Select " + file_names[i])
        if file_dialog.exec_():
            file_path = Path(file_dialog.selectedFiles()[0])
            file_paths.append(file_path)
        else:
            QMessageBox.warning(None, "Error", "Please select a file.")
            return
    run_solidity(*file_paths)
