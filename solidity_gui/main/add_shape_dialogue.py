"""User interface elements for adding simple geometric shapes."""

from typing import Any

from marshmallow.validate import Length
from pubsub import pub

from .forms import SimpleFormDialog
from .forms.fields import StrField
from .geometry import Component, Shape


class AddShapeDialog(SimpleFormDialog):
    """Generic dialog for creating a simple geometric shape.

    Dialog contents are generated from the specified geometry.Shape.
    """

    def __init__(self, shape: Shape, **kwargs: Any):
        """Initialise a new dialog.

        Args:
          shape: template shape used to generate input fields
        """
        super().__init__(
            type(
                "ExtendForm",
                (shape.form,),
                dict(label=StrField(validators=[Length(min=1)])),
            ),  # add label field to form class
            **kwargs,
        )
        self.shape = shape
        self.setWindowTitle(f"Add {shape.name}")

    def _ok_clicked(self) -> None:
        """Signal handler for clicking ok button."""
        if data := super()._ok_clicked():
            label = data.pop("label")
            component = Component(self.shape.name, label, data)
            pub.sendMessage("geometry.update", component=component)
            self.close()
