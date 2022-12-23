"""Entry point for the program.

It launches the PySide app, creates and displays the main window.
"""

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    from .main.main_window import MainWindow

    app = QApplication()
    window = MainWindow()

    app.exec()
