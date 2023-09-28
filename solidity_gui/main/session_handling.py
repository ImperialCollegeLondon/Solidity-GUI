"""Module for handling the saving and loading of sessions."""

import logging
import pickle

from marshmallow.validate import Length
from pubsub import pub
from PySide6.QtWidgets import QFileDialog, QWidget

from .condition import condition_assignment_datastore, condition_datastore
from .forms import Form, SimpleFormDialog
from .forms.fields import StrField
from .gmsh_process import GmshProcess, gmsh_process_datastore
from .material import material_assignment_datastore, material_datastore
from .meshes import mesh_datastore


class SessionNameForm(Form):
    """Form for collecting the name of the session."""

    name = StrField("Session Name", validators=[Length(min=1, max=20)])


class SessionNameDialog(SimpleFormDialog):
    """Dialog to display a SessionNameForm instance."""

    def _ok_clicked(self) -> None:
        if super()._ok_clicked():
            self.close()


def save_session(parent: QWidget) -> None:
    """Save the current session to a file."""
    form_dialog = SessionNameDialog(SessionNameForm)
    form_dialog.setWindowTitle("Set Session Name")
    try:
        form_data = form_dialog.run()
    except ValueError:
        return

    session_name = form_data["name"]

    print(mesh_datastore)

    with open(f"{session_name}.pickle", "wb") as session_file:
        pickle.dump(
            {
                "meshes": mesh_datastore,
                "material_assignments": material_assignment_datastore,
                "materials": material_datastore,
                "condition_assignments": condition_assignment_datastore,
                "conditions": condition_datastore,
            },
            session_file,
        )

    for mesh_name, gmsh_process in gmsh_process_datastore.items():
        gmsh_process.call_function(
            "export_geometry", filename=f"{session_name}_{mesh_name}.brep"
        )


def load_session(parent: QWidget) -> None:
    """Load a session from a file."""
    filename, _ = QFileDialog.getOpenFileName(
        parent,
        caption="Select a session file",
        filter="Session files (*.pickle)",
    )
    if not filename:
        return

    print(filename)

    with open(filename, "rb") as session_file:
        session_data = pickle.load(session_file)
        mesh_datastore.update(session_data["meshes"])
        for mesh_name, mesh in mesh_datastore.items():
            # Get the filename, minus the extension
            session_name = filename.split(".")[0]
            gmsh_process = GmshProcess(mesh_name)
            gmsh_process.start()
            gmsh_process_datastore[mesh_name] = gmsh_process

            logging.info(f"Importing geometry from file: {session_name}_{mesh_name}")
            mesh = gmsh_process.call_function(
                "import_geometry",
                geom_name=mesh_name,
                filename=f"{session_name}_{mesh_name}.brep",
            )
            pub.sendMessage("add_component.finish", mesh_name=mesh_name, obj=mesh)
            pub.sendMessage("session.load", mesh_name=mesh_name, mesh=mesh)
        material_assignment_datastore.update(session_data["material_assignments"])
        material_datastore.update(session_data["materials"])
        condition_assignment_datastore.update(session_data["condition_assignments"])
        condition_datastore.update(session_data["conditions"])
