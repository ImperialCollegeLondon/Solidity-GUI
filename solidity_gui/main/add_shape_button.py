"""Module for AddMeshButton.

This module is only a temporary placeholder for demonstration purposes.
"""

from typing import Any

from meshio import Mesh
from PySide6.QtWidgets import QPushButton

from . import signals
from .add_shape_dialogue import AddShapeDialog
from .geometry import SHAPES


class AddShapeButton(QPushButton):
    """Button that creates an AddShapeDialog when pressed."""

    def __init__(self, shape_name: str, *args: Any, **kwargs: Any) -> None:
        """Initialise a new button.

        Args:
          shape_name: shape that will be created
        """
        super().__init__(f"Add {shape_name}", *args, **kwargs)
        self.shape_name = shape_name
        self.clicked.connect(self._click_handler)

        signals.mesh.begin_meshing.connect(self._disable)

    def _click_handler(self) -> None:
        """Create dialog on click."""
        AddShapeDialog(SHAPES[self.shape_name]).exec_()

    def _disable(self, mesh: Mesh = None) -> None:
        self.setDisabled(True)
