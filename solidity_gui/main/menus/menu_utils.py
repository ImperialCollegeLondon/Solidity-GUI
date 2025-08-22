"""Utility functions for creating menu items."""

from collections.abc import Callable

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

from ..add_shape_dialogue import AddShapeDialog
from ..geometry import SHAPES


def create_action(menu: QMenu, label: str, callback: Callable) -> QAction:
    """Create a new action."""
    action = QAction(label, menu)
    action.triggered.connect(callback)
    return action


def create_shape_action(menu: QMenu, label: str) -> QAction:
    """Create a new action for adding a shape."""

    def callback() -> None:
        AddShapeDialog(SHAPES[label]).exec_()

    return create_action(menu, f"Add {label.capitalize()}", callback)
