"""Code to create a button which resets orientation of a VTKWindow."""
from typing import Any

from PySide6.QtWidgets import QPushButton

from .vtk_window import VTKWindow


class ResetViewWidget(QPushButton):
    """A button which resets a camera orientation for a given VTKWindow."""

    def __init__(self, vtk_window: VTKWindow, *args: Any, **kwargs: Any) -> None:
        """Create a new ResetViewWidget.

        Args:
            vtk_window: The VTKWindow which the button will contorl
        """
        super().__init__("Reset view", *args, **kwargs)

        self.intitial_camera_orientation = vtk_window.get_camera_orientation()
        self.vtk_window = vtk_window
        self.clicked.connect(self._click_handler)

    def _click_handler(self) -> None:
        self.vtk_window.set_camera_orientation(self.intitial_camera_orientation)
