"""Global Qt signals."""
from meshio import Mesh
from PySide6.QtCore import QObject, Signal

from ..geometry import Component
from .meshing import MeshingSignals


class _CameraSignals(QObject):
    reorient = Signal(object, object)
    """Reorient the camera.
    Args:
        orientation_vector
        up_vector
    """

    reset = Signal()


class _GeometrySignals(MeshingSignals):
    start_update = Signal(Component)
    updated = Signal(Mesh)


class _MeshSignals(MeshingSignals):
    create = Signal()
    select = Signal(str)
    updated = Signal(Mesh)


camera = _CameraSignals()
geometry = _GeometrySignals()
mesh = _MeshSignals()
