"""This module provides functionality to run Solidity."""
from PySide6.QtWidgets import QFileDialog, QMessageBox
import subprocess


def run_solidity_dialog():
    file_paths = []
    file_names = ["BST.Y3D", "layout.txt", "pellet.txt", "mat.txt"]
    for i in range(4):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setWindowTitle("Select " + file_names[i])
        if file_dialog.exec_():
            file_paths.append(file_dialog.selectedFiles()[0])
        else:
            QMessageBox.warning(None, "Error", "Please select a file.")
            return
    subprocess.run(["python", "-m", "solidity_gui.solidity"] + file_paths)
