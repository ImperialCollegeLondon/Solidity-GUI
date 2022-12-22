"""User interface elements for adding simple geometric shapes."""

from dataclasses import dataclass

from pubsub import pub
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout

@dataclass
class ClippingParameters:
    """Class for storing clipping parameters.

    Attributes:
        near: distance of near clipping plane from camera
        far: distance of far clipping plane from camera
    """

    near: float
    far: float

class ClippingPlanesDialog(QDialog):
    """Dialog for setting the clipping planes."""

    def __init__(self):
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle(f"Set clipping planes")
        layout = QVBoxLayout()
        self.setLayout(layout)

        # add widgets for near plane input
        self.near_field_label = QLabel("Near:")
        self.near_field_input = QLineEdit()
        layout.addWidget(self.near_field_label)
        layout.addWidget(self.near_field_input)

        # add widgets for far plane input
        self.far_field_label = QLabel("Far:")
        self.far_field_input = QLineEdit()
        layout.addWidget(self.far_field_label)
        layout.addWidget(self.far_field_input)

        # add ok and close buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Apply | QDialogButtonBox.Cancel
        )

        self.button_box.accepted.connect(self._apply_clicked)  # type: ignore[attr-defined]
        self.button_box.rejected.connect(self.close)  # type: ignore[attr-defined]
        layout.addWidget(self.button_box)

    def _apply_clicked(self) -> None:
        """Signal handler for clicking apply button."""
        clipping_parameters = ClippingParameters(self.near_field_input.text(), self.far_field_input.text())
        pub.sendMessage("clipping.update", clipping_parameters)
        self.close()
