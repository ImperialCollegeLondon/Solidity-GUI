"""User interface elements for adding simple geometric shapes."""

from dataclasses import dataclass

from pubsub import pub
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QLabel, QVBoxLayout

from .vtk_window import VTKWindow

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

    def __init__(self, vtk_window: VTKWindow):
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle(f"Set clipping planes")
        layout = QVBoxLayout()
        self.setLayout(layout)

        current_clipping_range = vtk_window.ren.GetActiveCamera().GetClippingRange()

        # add widgets for near plane input
        self.near_field_label = QLabel("Near:")
        self.near_field_input = QDoubleSpinBox()
        self.near_field_input.setMinimum(0.0)
        self.near_field_input.setMaximum(current_clipping_range[1]-0.01)
        self.near_field_input.setValue(current_clipping_range[0])
        self.near_field_input.setKeyboardTracking(False)
        self.near_field_input.valueChanged.connect(self._near_clipping_plane_value_change)
        layout.addWidget(self.near_field_label)
        layout.addWidget(self.near_field_input)

        # add widgets for far plane input
        self.far_field_label = QLabel("Far:")
        self.far_field_input = QDoubleSpinBox()
        self.far_field_input.setMinimum(current_clipping_range[0]+0.01)
        self.far_field_input.setMaximum(1000.0)
        self.far_field_input.setValue(current_clipping_range[1])
        self.far_field_input.setKeyboardTracking(False)
        self.far_field_input.valueChanged.connect(self._far_clipping_plane_value_change)
        layout.addWidget(self.far_field_label)
        layout.addWidget(self.far_field_input)

        # add ok and close buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Apply | QDialogButtonBox.Cancel
        )

        # The ApplyRole doesn't emit a signal (unlike the rejected() signal emitted by the close button)
        # So we need to connect to it directly
        self.button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_clicked)
        self.button_box.rejected.connect(self.close)  # type: ignore[attr-defined]
        layout.addWidget(self.button_box)

    def _apply_clicked(self) -> None:
        """Signal handler for clicking apply button."""
        print("click apply")
        clipping_parameters = ClippingParameters(self.near_field_input.text(), self.far_field_input.text())
        pub.sendMessage("clipping.update", clipping_parameters=clipping_parameters)
        self.close()

    def _near_clipping_plane_value_change(self) -> None:
        pub.sendMessage("near_clipping_plane_value_changed", value=self.near_field_input.value())
        self.far_field_input.setMinimum(self.near_field_input.value()+0.01)

    def _far_clipping_plane_value_change(self) -> None:
        pub.sendMessage("far_clipping_plane_value_changed", value=self.far_field_input.value())
        self.near_field_input.setMaximum(self.far_field_input.value()-0.01)
