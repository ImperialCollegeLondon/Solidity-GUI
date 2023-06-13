"""Unit tests for SolidityGUI."""
import sys
from logging import getLogger

if sys.platform == "linux":
    import os

    # Force Qt to use X11 backend, even if we're running on Wayland, as VTK requires it.
    # Qt does have an "offscreen" backend which is ideal for running tests with, but
    # sadly VTK can't use it either.
    os.environ["QT_QPA_PLATFORM"] = "xcb"

# Disable flake8 logger as it can be rather verbose
getLogger("flake8").propagate = False
