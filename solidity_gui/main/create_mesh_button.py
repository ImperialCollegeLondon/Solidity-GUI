"""Module for AddMeshButton.

This module is only a temporary placeholder for demonstration purposes.
"""

from typing import Any

from meshio import Mesh
from pubsub import pub
from PySide6.QtWidgets import QPushButton


class CreateMeshButton(QPushButton):
    """Button that triggers mesh generation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialise a new button."""
        super().__init__("Generate mesh", *args, **kwargs)
        self.clicked.connect(self._click_handler)
        pub.subscribe(self._disable, "mesh.updated")

    def _click_handler(self) -> None:
        """Send 'mesh.create' signal via pubsub."""
        pub.sendMessage("mesh.create")

    def _disable(self, mesh: Mesh = None) -> None:
        self.setDisabled(True)
