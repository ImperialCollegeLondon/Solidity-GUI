"""Module for the AssignPropertiesDialog class."""
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from .material import (
    MaterialAssignment,
    material_assignment_datastore,
    material_datastore,
)
from .meshes import mesh_datastore


class AssignPropertiesDialog(QDialog):
    """Dialog for assigning properties to geometries."""

    def __init__(self) -> None:
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle("Assign Properties")

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

        self.select_component_combo.addItems(
            [
                key
                for mesh in mesh_datastore.values()
                for key, value in mesh.cell_sets.items()
                if value[2] is not None
            ]
        )
        for key, material in material_datastore.items():
            self.select_material_combo.addItem(material.name, userData=key)

    def _save_clicked(self) -> None:
        selected_component_value = self.select_component_combo.currentText()
        selected_material_value = self.select_material_combo.currentData()
        if not selected_component_value or selected_material_value is None:
            return
        assignment = MaterialAssignment(
            material_id=selected_material_value, cell_set_name=selected_component_value
        )
        material_assignment_datastore.add(assignment)
        self.close()
