"""Infrastructure supporting loading geometry data from a file."""

import logging

from marshmallow.validate import Length, Range
from pubsub import pub
from PySide6.QtWidgets import QFileDialog, QWidget

from .error_message import display_error_message
from .forms import Form, SimpleFormDialog
from .forms.fields import StrField, BoolField, FloatField
from .gmsh_process import GmshProcess, gmsh_process_datastore


class GeometryNameForm(Form):
    """Form for collecting the name of new geometry component."""

    name = StrField("Component Label", validators=[Length(min=1, max=20)])
    resurface = BoolField(
        "Find surfaces", description="Should the surfaces be automatically discovered?"
    )
    threshold_angle = FloatField(
        "Threshold angle (deg)",
        description="Maximum angle between adjacent elements in the same surface",
        validators=[Range(min=0, max=90, max_inclusive=False)],
    )


class GeometryNameDialog(SimpleFormDialog):
    """Dialog to display a GeometryNameForm instance."""

    def _ok_clicked(self) -> None:
        if super()._ok_clicked():
            self.close()


def load_geometry(parent: QWidget) -> None:
    """Load and a new geometry into a GmshProcess and display the resulting mesh."""
    filename, _ = QFileDialog.getOpenFileName(
        parent,
        caption="Select gmsh geometry file",
        filter="GMSH geometry (*.geo *.step *.brep *.msh)",
    )
    if not filename:
        return

    form_dialog = GeometryNameDialog(
        GeometryNameForm, initial_data={"threshold_angle": 30}
    )
    form_dialog.setWindowTitle("Set Component Name")
    try:
        form_data = form_dialog.run()
    except ValueError:
        return

    geom_name = form_data["name"]
    resurface = form_data["resurface"]
    threshold = form_data["threshold_angle"]

    if geom_name in gmsh_process_datastore:
        display_error_message("A component with that name already exists.")
        return

    # assert geom_name not in gmsh_process_datastore
    gmsh_process = GmshProcess(geom_name)
    gmsh_process.start()
    gmsh_process_datastore[geom_name] = gmsh_process

    logging.info(f"Importing geometry from file: {filename}")
    mesh = gmsh_process.call_function(
        "import_geometry", geom_name=geom_name, filename=filename, resurface=resurface
    )
    pub.sendMessage("add_component.finish", mesh_name=geom_name, obj=mesh)
