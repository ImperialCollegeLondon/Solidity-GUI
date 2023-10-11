"""Defines the MeshSelectionComboBox subclass MeshMaskComboBox."""
from typing import Any

from meshio import Mesh
from pubsub import pub

from .mesh_selection_combobox import MeshSelectionComboBox
from .meshes import mesh_datastore


class MeshMaskComboBox(MeshSelectionComboBox):
    """QComboBox for masking a mesh, populated from a mesh's cell_sets."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create new MeshMaskComboBox."""
        super().__init__(*args, **kwargs)

        self.setPlaceholderText("--Show All--")

        pub.subscribe(self._set_meshes, "meshes.update")

    def _set_meshes(self, key: str, value: Mesh) -> None:
        """Update the list of meshes in the combo box."""
        self.clear()
        self.addItem("--Show All--")
        self.addItems(mesh_datastore.keys())
        self.setCurrentIndex(-1)
