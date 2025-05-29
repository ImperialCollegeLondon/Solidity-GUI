"""Module for checking if the current machine is allowed to run the application."""

import logging
import uuid
from datetime import date

from solidity_gui.config import ALLOWED_MAC_ADDRESSES


def _has_expired(mac_address: str) -> bool:
    """Check whether the trial period for this program has elapsed."""
    expiry = ALLOWED_MAC_ADDRESSES.get(mac_address)
    # Not a trial version
    if expiry is None:
        return False

    expiry_date = date.fromisoformat(expiry)
    if date.today() > expiry_date:
        logging.warn(
            f"This trial version expired on {expiry_date.strftime('%d %b %Y')}."
        )
        return True

    logging.warn(
        f"This trial version will expire on {expiry_date.strftime('%d %b %Y')}."
    )
    return False


def _get_mac_address() -> str:
    """Get the MAC address of the current machine."""
    try:
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ":".join([mac[e : e + 2].upper() for e in range(0, 11, 2)])
    except Exception as e:
        raise RuntimeError("Error occurred while trying to retrieve MAC address") from e


def is_mac_address_allowed() -> tuple[bool, str]:
    """Check if the current MAC address is allowed to run the application."""
    mac_address = _get_mac_address()
    if not ALLOWED_MAC_ADDRESSES:
        return True, ""
    return (
        mac_address in ALLOWED_MAC_ADDRESSES and not _has_expired(mac_address),
        mac_address,
    )
