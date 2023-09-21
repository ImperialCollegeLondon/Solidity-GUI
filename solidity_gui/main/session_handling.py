"""Module for handling the saving and loading of sessions."""

import pickle

from pubsub import pub

from .condition import condition_assignment_datastore, condition_datastore
from .material import material_assignment_datastore, material_datastore
from .meshes import mesh_datastore


def save_session() -> None:
    """Save the current session to a file."""
    with open("session.pickle", "wb") as session_file:
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


def load_session() -> None:
    """Load a session from a file."""
    with open("session.pickle", "rb") as session_file:
        session_data = pickle.load(session_file)
        mesh_datastore.update(session_data["meshes"])
        for mesh_name, mesh in mesh_datastore.items():
            pub.sendMessage("session.load", mesh_name=mesh_name, mesh=mesh)
        material_assignment_datastore.update(session_data["material_assignments"])
        material_datastore.update(session_data["materials"])
        condition_assignment_datastore.update(session_data["condition_assignments"])
        condition_datastore.update(session_data["conditions"])
