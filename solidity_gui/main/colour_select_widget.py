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
        pub.subscribe(self._set_items, "add_component.finish")
        pub.subscribe(self._set_items, "generate_mesh.finish")
        pub.subscribe(self._select_handler, "mesh.rendered")
        pub.subscribe(self._clear, "mesh.create")

    def _select_handler(self, mesh: Mesh = None) -> None:
        selectedValue = self.currentText()
        if not selectedValue:
            return

        pub.sendMessage("mesh.select", selection_name=selectedValue)

    def _clear(self, size: float) -> None:
        self.clear()

    def _set_items(self, mesh_name: str, obj: Mesh) -> None:
        self.addItems(obj.cell_sets.keys())
