"""Code for a QComboBox widget to highlight cell_sets in a VTKWindow."""
from typing import Any

from meshio import Mesh
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QComboBox

from . import signals


class ColourSelectWidget(QComboBox):
    """QComboBox for highlighting a surface, populated from a mesh's cell_sets."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create new ColourSelectWidget."""
        super().__init__(*args, **kwargs)

        self.currentTextChanged.connect(self._select_handler)
        signals.geometry.updated.connect(self._set_items)
        signals.mesh.updated.connect(self._select_handler)

    def _select_handler(self, mesh: Mesh = None) -> None:
        if selection_name := self.currentText():
            signals.mesh.emit(selection_name)

    @Slot()
    def _set_items(self, mesh: Mesh) -> None:
        self.addItems(mesh.cell_sets.keys())
