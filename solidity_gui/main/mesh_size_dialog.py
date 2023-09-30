"""GUI components for specification of global mesh size."""

import logging

from marshmallow import validate
from pubsub import pub

from .forms import Form, SimpleFormDialog
from .forms.fields import FloatField
from .mesh_sizes import mesh_size_datastore


class MeshResolutionForm(Form):
    """Form for collecting for mesh size data."""

    size = FloatField(
        display_name="Mesh Size",
        validators=[validate.Range(min=0, min_inclusive=False)],
    )


class MeshSizeDialog(SimpleFormDialog):
    """Dialog request mesh size data from the user."""

    def __init__(self) -> None:
        """Create a new MeshSizeDialog instance."""
        super().__init__(form_class=MeshResolutionForm)

    def _ok_clicked(self) -> None:
        """Process form and send 'mesh.create' signal via pubsub."""
        if data := super()._ok_clicked():
            logging.info(f"Creating mesh with default resolution {data['size']}")
            pub.sendMessage("geometry.finalise")
            pub.sendMessage(
                "mesh.create",
                mesh_sizes=mesh_size_datastore.values(),
                default_size=data["size"],
            )
            self.close()
