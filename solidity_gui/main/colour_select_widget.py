"""Code for a QComboBox widget to highlight cell_sets in a VTKWindow."""
from typing import Any

from meshio import Mesh
from pubsub import pub
from PySide6.QtWidgets import QComboBox


class ColourSelectWidget(QComboBox):
    """QComboBox for highlighting a surface, populated from a mesh's cell_sets."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create new ColourSelectWidget.

        Args:
            vtk_window: The VTKWindow which this widget interacts with.
        """
        super().__init__(*args, **kwargs)

        self.currentTextChanged.connect(self._select_handler)
        pub.subscribe(self._set_items, "mesh.updated")

    def _select_handler(self) -> None:
        selectedValue = self.currentText()
        if not selectedValue:
            return

        pub.sendMessage("mesh.select", selection_name=selectedValue)

    def _set_items(self, mesh: Mesh) -> None:
        self.clear()
        self.addItems(mesh.cell_sets.keys())
