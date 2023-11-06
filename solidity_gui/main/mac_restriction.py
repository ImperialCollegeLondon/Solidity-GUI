"""Module for checking if the current machine is allowed to run the application."""

import sys
import uuid

from PySide6.QtWidgets import QMessageBox

from solidity_gui.config import ALLOWED_MAC_ADDRESSES

from ..config import APP_NAME


# Retrieve the MAC address of the current machine
def _get_mac_address() -> str:
    """Get the MAC address of the current machine."""
    try:
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ":".join([mac[e : e + 2].upper() for e in range(0, 11, 2)])
    except Exception as e:
        raise RuntimeError("Error occurred while trying to retrieve MAC address") from e


# Check if the current MAC address is allowed
def _is_mac_address_allowed() -> bool:
    """Check if the current MAC address is allowed to run the application."""
    if not ALLOWED_MAC_ADDRESSES:
        return True
    return _get_mac_address() in ALLOWED_MAC_ADDRESSES


def _show_expiry_dialog() -> None:
    """Show a dialog box when the trial version of the application has expired."""
    err_box = QMessageBox()
    err_box.setIcon(QMessageBox.Icon.Critical)
    err_box.setWindowTitle("Access restricted")
    err_box.setText(f"The machine you are using is not authorised to run {APP_NAME}.")
    err_box.exec_()


def quit_if_no_access() -> None:
    """Quit the application if the current machine is not allowed to run it."""
    if not _is_mac_address_allowed():
        _show_expiry_dialog()

        sys.exit(1)
