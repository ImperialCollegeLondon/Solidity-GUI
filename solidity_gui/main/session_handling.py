"""Module for handling the saving and loading of sessions."""

import logging
import pickle
from pathlib import Path

from pubsub import pub
from PySide6.QtWidgets import QFileDialog, QWidget

from .condition import condition_assignment_datastore, condition_datastore
from .control import control_datastore
from .gmsh_process import GmshProcess, gmsh_process_datastore
from .initial_condition import (
    initial_condition_assignment_datastore,
    initial_condition_datastore,
)
from .material import material_assignment_datastore, material_datastore
from .meshes import mesh_datastore


def save_session(parent: QWidget) -> None:
    """Save the current session to a file."""
    session_filename, _ = QFileDialog.getSaveFileName(
        parent,
        caption="Save session",
        filter="Session files (*.pickle)",
    )

    # If extension not given, automatically add it
    if not session_filename.endswith(".pickle"):
        session_filename += ".pickle"

    with open(session_filename, "wb") as session_file:
        pickle.dump(
            {
                "meshes": mesh_datastore,
                "material_assignments": material_assignment_datastore,
                "materials": material_datastore,
                "condition_assignments": condition_assignment_datastore,
                "conditions": condition_datastore,
                "initial_condition_assignments": initial_condition_assignment_datastore,
                "initial_conditions": initial_condition_datastore,
                "controls": control_datastore,
            },
            session_file,
        )

    session_name = Path(session_filename).parent / Path(session_filename).stem
    for mesh_name, gmsh_process in gmsh_process_datastore.items():
        for extension in ["brep", "msh"]:
            gmsh_process.call_function(
                "write_file",
                filename=f"{session_name}_{mesh_name}.{extension}",
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
            # geom_mesh = gmsh_process.call_function(
            #     "import_geometry",
            #     geom_name=mesh_name,
            #     filename=f"{session_name}_{mesh_name}.brep",
            # )
            gmsh_process.call_function(
                "open_file", filename=f"{session_name}_{mesh_name}.brep"
            )
            gmsh_process.call_function(
                "merge_mesh", filename=f"{session_name}_{mesh_name}.msh"
            )

            pub.sendMessage("session.load", mesh_name=mesh_name, mesh=mesh)
            pub.sendMessage("session.enable_export_bst", mesh_name=mesh_name, obj=mesh)
        material_assignment_datastore.update(session_data["material_assignments"])
        material_datastore.update(session_data["materials"])
        condition_assignment_datastore.update(session_data["condition_assignments"])
        condition_datastore.update(session_data["conditions"])
        initial_condition_assignment_datastore.update(
            session_data["initial_condition_assignments"]
        )
        initial_condition_datastore.update(session_data["initial_conditions"])
        control_datastore.update(session_data["controls"])
