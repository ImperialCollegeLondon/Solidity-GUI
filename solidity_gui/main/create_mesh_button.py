"""Module for AddMeshButton.

This module is only a temporary placeholder for demonstration purposes.
"""

from typing import Any

from PySide6.QtWidgets import QPushButton

from . import signals


class CreateMeshButton(QPushButton):
    """Button that triggers mesh generation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialise a new button."""
        super().__init__("Generate mesh", *args, **kwargs)
        self.clicked.connect(signals.mesh.create.emit)
        self.setDisabled(True)

        signals.mesh.begin_meshing.connect(lambda: self.setDisabled(True))
        signals.geometry.updated.connect(lambda: self.setDisabled(False))
