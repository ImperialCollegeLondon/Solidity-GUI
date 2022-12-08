"""Entry point for the program.

It launches the PySide app, creates and displays the main window.
"""
from PySide6.QtWidgets import QApplication

from .main.main_window import MainWindow

app = QApplication()
window = MainWindow()

app.exec()
