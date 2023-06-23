"""Simple form for creating a new material."""

import logging

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from .edit_material_dialog import EditMaterialDialog
from .material import Material, MaterialDatastore, material_datastore


class CreateMaterialDialog(QDialog):
    """Dialog for creating a material."""

    def __init__(self, materials: MaterialDatastore) -> None:
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle("Create new material")

        layout = QVBoxLayout()
        self.setLayout(layout)

        name_label = QLabel("Material name:")
        self.name_input = QLineEdit()

        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        self.materials = materials

        # add ok and close buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        self.button_box.accepted.connect(self._ok_clicked)  # type: ignore[attr-defined]
        self.button_box.rejected.connect(self.close)  # type: ignore[attr-defined]
        layout.addWidget(self.button_box)

    def _ok_clicked(self) -> None:
        material_name = self.name_input.text()

        # validate material name
        if not material_name.isalnum():
            QMessageBox.warning(
                self, "Invalid input", "Input must contain only letters and numbers."
            )
            return

        if not material_name:
            QMessageBox.warning(self, "Invalid input", "Name cannot be empty.")
            return

        if material_name.strip().lower() in [
            material.name.strip().lower() for material in self.materials.values()
        ]:
            QMessageBox.warning(self, "Invalid input", "Name already exists!")
            return

        material = Material(name=material_name)
        material_datastore.add(material)
        self.close()

        logging.info(f'Added new material "{material_name}"')

        # Open dialog to edit new material
        EditMaterialDialog(material).exec()
