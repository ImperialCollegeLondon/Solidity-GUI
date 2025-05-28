"""The main package, containing the code for running the GUI."""

from PySide6.QtWidgets import QApplication


def force_gui_refresh() -> None:
    """Forces the processing of gui task in the main loop.

    Mainly use to force showing the logs in the main window in real time. It is quick
    and dirty, and might slow down the application if used too frequently, so should be
    limited when there's something going on that takes a lot of time to run in order
    to provide some feedback to the user.
    """
    if app := QApplication.instance():
        app.processEvents()
