"""User interface elements for adding simple geometric shapes."""

from typing import List

from pubsub import pub
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout

from .geometry import Arg_Dict_Type, Arg_List_Type, Component, Shape


def _get_args(inputs: List[str], types: Arg_Dict_Type) -> Arg_List_Type:
    """Convert flat text data to structured typed input for geometry creation.

    Args:
      inputs: unstructured text values for conversion
      types: mapping of method arguments to expected types

    """
    args: Arg_List_Type = []
    iter_inputs = iter(inputs)

    for key, value in types.items():
        if isinstance(value, tuple):
            sub_args = []
            for type_ in value:
                sub_args.append(type_(next(iter_inputs)))
            args.append(sub_args)
        else:
            type_ = value
            args.append(type_(next(iter_inputs)))

    return args


class AddShapeDialog(QDialog):
    """Generic dialog for creating a simple geometric shape.

    Dialog contents are generated from the specified geometry.Shape.
    """

    def __init__(self, shape: Shape):
        """Initialise a new dialog.

        Args:
          shape: template shape used to generate input fields
        """
        super().__init__()
        self.shape = shape
        self.setWindowTitle(f"Add {shape.name}")
        layout = QVBoxLayout()
        self.setLayout(layout)

        # add widgets for label input
        self.label_field_label = QLabel("Label:")
        self.label_field_input = QLineEdit()
        layout.addWidget(self.label_field_label)
        layout.addWidget(self.label_field_input)

        # add widgets for arguments passed to pygmsh
        self.inputs = []
        for arg_name, arg_type in shape.args.items():
            layout.addWidget(QLabel(f"{arg_name}:"))
            if isinstance(arg_type, tuple):
                for type_ in arg_type:
                    input_widget = QLineEdit()
                    layout.addWidget(input_widget)
                    self.inputs.append(input_widget)
            else:
                input_widget = QLineEdit()
                layout.addWidget(input_widget)
                self.inputs.append(input_widget)

        # add ok and close buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        # mypy doesn't think accepted and rejected below are defined for some reason
        # some __getattr__ shenanigans from pyside?
        self.button_box.accepted.connect(self._ok_clicked)  # type: ignore[attr-defined]
        self.button_box.rejected.connect(self.close)  # type: ignore[attr-defined]
        layout.addWidget(self.button_box)

    def _ok_clicked(self) -> None:
        """Signal handler for clicking ok button."""
        label = self.label_field_input.text()
        args = _get_args([inp.text() for inp in self.inputs], self.shape.args)
        component = Component(self.shape.name, label, args)
        pub.sendMessage("geometry.update", component=component)
        self.close()
