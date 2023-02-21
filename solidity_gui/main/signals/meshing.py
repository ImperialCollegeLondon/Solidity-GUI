from meshio import Mesh
from PySide6.QtCore import QObject, Signal


class MeshingSignals(QObject):
    begin_meshing = Signal()
    end_meshing = Signal(Mesh)
