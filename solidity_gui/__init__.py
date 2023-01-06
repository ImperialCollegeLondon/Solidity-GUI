"""Entry point for the Solidity-GUI program.

Solidity-GUI is a software for preparing system geometries
in a mesh format for use by the Solidity tool.

Run the software with: python -m solidity_gui.
"""


def run() -> None:
    """Main entry point to program."""
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
    window.show()
    app.exec()
