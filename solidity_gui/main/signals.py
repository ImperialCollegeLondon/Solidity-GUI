"""Global Qt signals."""
from meshio import Mesh
from PySide6.QtCore import QObject, Signal

from .geometry import Component


class _GeometrySignals(QObject):
    start_update = Signal(Component)
    updated = Signal(Mesh)


geometry = _GeometrySignals()
