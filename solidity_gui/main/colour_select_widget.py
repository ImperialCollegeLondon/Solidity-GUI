"""Code for a QComboBox widget to highlight cell_sets in a VTKWindow."""
from typing import Any

from meshio import Mesh
from pubsub import pub
from PySide6.QtWidgets import QComboBox


class ColourSelectWidget(QComboBox):
    """QComboBox for highlighting a surface, populated from a mesh's cell_sets."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create new ColourSelectWidget."""
        super().__init__(*args, **kwargs)

        self.currentTextChanged.connect(self._select_handler)
        pub.subscribe(self._set_items, "geometry.updated")
        pub.subscribe(self._select_handler, "mesh.updated")

    def _select_handler(self, mesh: Mesh = None) -> None:
        selectedValue = self.currentText()
        if not selectedValue:
            return

        pub.sendMessage("mesh.select", selection_name=selectedValue)

    def _set_items(self, mesh: Mesh) -> None:
        self.addItems(mesh.cell_sets.keys())
