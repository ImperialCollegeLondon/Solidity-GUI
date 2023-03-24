"""Module for the AssignPropertiesDialog class."""
from typing import Dict

from meshio import Mesh
from pubsub import pub
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class AssignPropertiesDialog(QDialog):
    """Dialog for assigning properties to geometries."""

    def __init__(self) -> None:
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle("Assign Properties")

        self.assigned_materials: Dict[str, str] = {}

        component_label = QLabel("Component:")
        self.select_component_combo = QComboBox()
        self.select_component_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        material_label = QLabel("Material:")
        self.select_material_combo = QComboBox()
        self.select_material_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(component_label)
        layout.addWidget(self.select_component_combo)
        layout.addWidget(material_label)
        layout.addWidget(self.select_material_combo)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.button_box.rejected.connect(self.close)
        self.button_box.accepted.connect(self._save_clicked)

        layout.addWidget(self.button_box)

        pub.subscribe(self._set_components, "geometry.updated")
        pub.subscribe(self._add_material, "materials.add")
        pub.subscribe(self._remove_material, "materials.remove")

    def _set_components(self, mesh: Mesh) -> None:
        self.select_component_combo.addItems(
            [key for key, value in mesh.cell_sets.items() if value[2] is not None]
        )

    def _add_material(self, material: str) -> None:
        self.select_material_combo.addItem(material)

    def _remove_material(self, material: str) -> None:
        self.select_material_combo.removeItem(
            self.select_material_combo.findText(material)
        )

    def _save_clicked(self) -> None:
        selectedComponentValue = self.select_component_combo.currentText()
        selectedMaterialValue = self.select_material_combo.currentText()
        if not (selectedComponentValue and selectedMaterialValue):
            return

        self.assigned_materials[selectedComponentValue] = selectedMaterialValue
        self.close()
