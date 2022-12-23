"""Entry point for the program.

It launches the PySide app, creates and displays the main window.
"""

if __name__ == "__main__":
    import sys

    if sys.platform == "linux":
        import os

        # Force Qt to use X11 backend, even if we're running on Wayland, as VTK requires
        # it
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    from PySide6.QtWidgets import QApplication

    from .main.main_window import MainWindow

    app = QApplication()
    window = MainWindow()

    app.exec()
