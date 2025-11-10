"""Display error messages to the user."""

from PySide6.QtWidgets import QMessageBox, QWidget


def display_error_message(message: str, parent: QWidget | None = None) -> None:
    """Displays an error message to the user."""
    msg_box = QMessageBox(parent) if parent is not None else QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)  # type: ignore[attr-defined]
    msg_box.setText("Error")
    msg_box.setInformativeText(message)
    msg_box.setWindowTitle("Error")
    msg_box.exec_()
