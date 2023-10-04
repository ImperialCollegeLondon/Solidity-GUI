"""GUI components for specification of global mesh size."""

import logging
from operator import attrgetter

from marshmallow import validate
from pubsub import pub
from PySide6.QtWidgets import QDialogButtonBox, QLabel, QLayout

from .assignment_table import AssignmentTable
from .forms import Form, SimpleFormDialog
from .forms.fields import FloatField
from .forms.info import FormInfo
from .mesh_sizes import mesh_size_datastore


class MeshResolutionForm(Form):
    """Form for collecting for mesh size data."""

    size = FloatField(
        display_name="Mesh Size",
        description=(
            "This value is assigned to all components that do not have an entry in "
            "the table below"
        ),
        validators=[validate.Range(min=0, min_inclusive=False)],
    )


class MeshSizeDialog(SimpleFormDialog):
    """Dialog request mesh size data from the user."""

    def __init__(self) -> None:
        """Create a new MeshSizeDialog instance."""
        super().__init__(form_class=MeshResolutionForm)

    def _create_contents(self, form_info: FormInfo) -> QLayout:
        """Create the contents of the dialog from a FormInfo instance."""
        contents = self.form_renderer(form_info)
        contents.addWidget(QLabel("Assigned mesh sizes:"))
        table = AssignmentTable(["Size"], [attrgetter("size")])
        table.add_items(mesh_size_datastore.values())
        contents.addWidget(table)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel  # type: ignore[attr-defined]
        )
        contents.addWidget(button_box)
        button_box.accepted.connect(self._ok_clicked)  # type: ignore[attr-defined]
        button_box.rejected.connect(self._cancel_clicked)  # type: ignore[attr-defined]
        return contents

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
