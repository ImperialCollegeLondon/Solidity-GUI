"""Entry point for the Solidity-GUI program.

Solidity-GUI is a software for preparing system geometries
in a mesh format for use by the Solidity tool.

Run the software with: python -m solidity_gui.
"""


def run() -> None:
    """Main entry point to program."""
    import multiprocessing
    import sys

    from .logger import initialise_logging

    # Configure program log
    initialise_logging()

    if sys.platform == "linux":
        import os

        # Force Qt to use X11 backend, even if we're running on Wayland, as VTK requires
        # it
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    # Needed if you're using multiprocessing within a pyinstaller-built exe on Windows,
    # otherwise your main window will repeatedly open

    multiprocessing.freeze_support()

    # NB: We import PySide *after* setting QT_QPA_PLATFORM
    from PySide6.QtWidgets import QApplication

    from .main.main_window import MainWindow

    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()
