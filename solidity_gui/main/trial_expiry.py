"""Code for checking the trial expiry date and displaying a dialog if needed."""
import logging
import sys
from datetime import date

from PySide6.QtWidgets import QMessageBox

from ..config import APP_NAME, TRIAL_EXPIRY_DATE


def _has_expired() -> bool:
    """Check whether the trial period for this program has elapsed."""
    # Not a trial version
    if not TRIAL_EXPIRY_DATE:
        return False

    logging.warn(
        f"This trial version will expire on {TRIAL_EXPIRY_DATE.strftime('%d %b %Y')}."
    )

    return date.today() >= TRIAL_EXPIRY_DATE


def _show_expiry_dialog() -> None:
    err_box = QMessageBox()
    err_box.setIcon(QMessageBox.Icon.Critical)
    err_box.setWindowTitle("Your trial has ended")
    err_box.setText(
        f"Your trial of {APP_NAME} ended "
        f"on {TRIAL_EXPIRY_DATE.strftime('%d %b %Y')}. "  # type: ignore[union-attr]
        "The program will now exit."
    )
    err_box.exec_()


def quit_if_expired() -> None:
    """Show an error message and exit the program if the trial period has elapsed."""
    if _has_expired():
        _show_expiry_dialog()

        # Exit the program
        sys.exit()
