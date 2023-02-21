"""Global Qt signals."""
from meshio import Mesh
from PySide6.QtCore import QObject, Signal

from .geometry import Component


class _CameraSignals(QObject):
    reorient = Signal(object, object)
    """Reorient the camera.
    Args:
        orientation_vector
        up_vector
    """

    reset = Signal()


camera = _CameraSignals()


class _GeometrySignals(QObject):
    start_update = Signal(Component)
    updated = Signal(Mesh)


geometry = _GeometrySignals()
