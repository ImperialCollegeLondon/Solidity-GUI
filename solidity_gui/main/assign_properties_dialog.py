"""Module for the MaterialsManagerDialog class."""
from meshio import Mesh
from pubsub import pub
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QLabel, QVBoxLayout


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

        pub.subscribe(self._set_components, "geometry.updated")
        pub.subscribe(self._set_materials, "materials.add")

    def _set_components(self, mesh: Mesh) -> None:
        self.select_component_combo.addItems(mesh.cell_sets.keys())

    def _set_materials(self, material: str) -> None:
        self.select_material_combo.addItem(material)

    def _save_clicked(self):
        ...
