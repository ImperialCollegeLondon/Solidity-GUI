"""Simple form for creating a new material."""

from typing import Dict

from pubsub import pub
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from .edit_material_dialog import EditMaterialDialog
from .material import Material


class CreateMaterialDialog(QDialog):
    """Dialog for creating a material."""

    def __init__(self, materials: Dict[str, Material]) -> None:
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
            name.strip().lower() for name in self.materials.keys()
        ]:
            QMessageBox.warning(self, "Invalid input", "Name already exists!")
            return

        pub.sendMessage("materials.add", material=material_name)
        self.close()
        EditMaterialDialog(self.materials[material_name]).exec()
