"""Code to create a button which resets orientation of a VTKWindow."""
from typing import Any, Dict

from PySide6.QtWidgets import QPushButton
from vtk import vtkRenderer

from .vtk_window import VTKWindow


def set_orientation(ren: vtkRenderer, p: Dict[str, Any]) -> None:
    """Resets a camera orientation for a vtkRenderer.

    Args:
        ren: The vtkRenderer for which to set the new camera orientation
        p: The Dict containing the camera orientation details
    """
    camera = ren.GetActiveCamera()
    camera.SetPosition(p["position"])
    camera.SetFocalPoint(p["focal point"])
    camera.SetViewUp(p["view up"])
    camera.SetDistance(p["distance"])
    camera.SetClippingRange(p["clipping range"])


def get_orientation(ren: vtkRenderer) -> Dict[str, Any]:
    """Stores details on a camera orientation in a Dict.

    Args:
        ren: The vtkRenderer from which to fetch the camera orientation
    """
    p = dict()
    camera = ren.GetActiveCamera()
    p["position"] = camera.GetPosition()
    p["focal point"] = camera.GetFocalPoint()
    p["view up"] = camera.GetViewUp()
    p["distance"] = camera.GetDistance()
    p["clipping range"] = camera.GetClippingRange()
    p["orientation"] = camera.GetOrientation()
    return p


class ResetViewWidget(QPushButton):
    """A button which resets a camera orientation for a given VTKWindow."""

    def __init__(self, vtk_window: VTKWindow, *args: Any, **kwargs: Any) -> None:
        """Create a new ResetViewWidget.

        Args:
            vtk_window: The VTKWindow which the button will contorl
        """
        super().__init__("Reset view", *args, **kwargs)

        self.original_orientation = get_orientation(vtk_window.ren)
        self.vtk_window = vtk_window
        self.clicked.connect(self._click_handler)

    def _click_handler(self) -> None:
        set_orientation(self.vtk_window.ren, self.original_orientation)
        self.vtk_window.ren.ResetCamera()
        self.vtk_window.iren.ReInitialize()
