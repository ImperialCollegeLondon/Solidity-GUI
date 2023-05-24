"""This module provides functionality to run Solidity."""
from PySide6.QtWidgets import QFileDialog, QMessageBox
import subprocess


def run_solidity_dialog():
    file_dialog = QFileDialog()
    file_dialog.setFileMode(QFileDialog.ExistingFiles)
    if file_dialog.exec_():
        file_paths = file_dialog.selectedFiles()
        print(file_paths)
        if len(file_paths) == 4:
            subprocess.run(
                [
                    "python",
                    "-m",
                    "solidity_gui.solidity",
                    file_paths[0],
                    file_paths[1],
                    file_paths[2],
                    file_paths[3],
                ]
            )
        else:
            QMessageBox.warning("Error", "Please select 4 files.")
