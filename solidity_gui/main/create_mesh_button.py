"""Module for AddMeshButton.

This module is only a temporary placeholder for demonstration purposes.
"""

from typing import Any

from meshio import Mesh
from pubsub import pub
from PySide6.QtWidgets import QPushButton

from .mesh_size_dialog import MeshSizeDialog


class CreateMeshButton(QPushButton):
    """Button that triggers mesh generation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialise a new button."""
        super().__init__("Generate mesh", *args, **kwargs)
        self.clicked.connect(self._click_handler)
        self.setDisabled(True)
        pub.subscribe(self._disable, "mesh.create")
        pub.subscribe(self._enable, "geometry.updated")
        pub.subscribe(self._disable_no_args, "mesh.finalise")

    def _disable_no_args(self) -> None:
        self.setDisabled(True)

    def _click_handler(self) -> None:
        """Display a MeshSizeDialog to the user."""
        MeshSizeDialog().exec_()

    def _disable(self, mesh_sizes: object, default_size: object) -> None:
        self.setDisabled(True)

    def _enable(self, mesh_name: str, mesh: Mesh = None) -> None:
        self.setDisabled(False)
