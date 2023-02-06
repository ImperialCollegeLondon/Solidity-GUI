from pubsub import pub
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout

class CreateMaterialDialog(QDialog):
    """Dialog for creating a material."""

    def __init__(self):
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle(f"Create new material")

        layout = QVBoxLayout()
        self.setLayout(layout)

        name_label = QLabel("Material name:")
        self.name_input = QLineEdit()

        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        # add ok and close buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        self.button_box.accepted.connect(self._ok_clicked)  # type: ignore[attr-defined]
        self.button_box.rejected.connect(self.close)  # type: ignore[attr-defined]
        layout.addWidget(self.button_box)

    def _ok_clicked(self):
        pub.sendMessage("materials.add", material=self.name_input.text())
        self.close()