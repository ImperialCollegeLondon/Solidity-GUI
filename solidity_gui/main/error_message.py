"""Display error messages to the user."""

from PySide6.QtWidgets import QMessageBox


def display_error_message(message: str) -> None:
    """Displays an error message to the user."""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)  # type: ignore[attr-defined]
    msg_box.setText("Error")
    msg_box.setInformativeText(message)
    msg_box.setWindowTitle("Error")
    msg_box.exec_()
