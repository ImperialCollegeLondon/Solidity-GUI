"""This module provides functionality to generate an input file for Solidity."""
from pathlib import Path
from typing import Any, Dict, Mapping

import numpy as np
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from meshio import Mesh
from PySide6.QtWidgets import QMessageBox

from .. import config
from .gmsh_process import gmsh_process_datastore
from .material import (
    MaterialAssignment,
    material_assignment_datastore,
    material_datastore,
)
from .meshes import mesh_datastore

env = Environment(
    loader=FileSystemLoader(str(Path(__file__).absolute().parent.parent / "templates")),
    undefined=StrictUndefined,
)


class SystemValidationError(Exception):
    """Raised when there is a problem with the system."""

    pass


def write_file(file_content: str, output_file: Path | str) -> None:
    """Write the contents of file_content to file.

    Raises:
        IOError: If there is a problem writing to the output file.
    """
    with open(output_file, "w") as f:
        f.write(file_content)


def generate_nodes_data(
    meshes: Mapping[str, Mesh], surface_nodes: Mapping[str, np.ndarray]
) -> Dict[str, Any]:
    """Prepare data needed for template renderering."""
    num_nodes = sum(mesh.points.shape[0] for mesh in meshes.values())
    all_nodes = np.concatenate([mesh.points for mesh in meshes.values()], axis=0)

    combined_surface_nodes = np.array([])
    incr = 0
    for mesh_name in meshes:
        mesh_surface_nodes = surface_nodes[mesh_name]
        mesh_surface_nodes = mesh_surface_nodes + incr
        combined_surface_nodes = np.concatenate(
            [combined_surface_nodes, mesh_surface_nodes]
        )
        incr += meshes[mesh_name].points.shape[0]

    surface_node_flags = np.zeros((num_nodes,), dtype="uint64")
    surface_node_flags[combined_surface_nodes.astype("uint64")] = 1

    return dict(
        num_nodes=num_nodes,
        nodes=all_nodes,
        surface_node_flags=surface_node_flags,
    )


def fetch_material_assignments(
    mesh: Mesh, material_assignments: Mapping[int, MaterialAssignment]
) -> np.ndarray:
    """Fetches the material assignments for a given mesh."""
    cell_materials_list = []
    for assignment in material_assignments.values():
        cell_ids = mesh.cell_sets_dict[assignment.cell_set_name]["tetra"]
        cell_materials_list.append(
            np.array([cell_ids, np.full_like(cell_ids, assignment.material_id)]).T
        )
    if cell_materials_list:
        cell_materials = np.concatenate(cell_materials_list, axis=0)
    else:
        cell_materials = np.empty((0, 2), dtype="uint64")

    return cell_materials


def check_unassigned_cells(cell_materials: np.ndarray, mesh: Mesh) -> None:
    """Checks if there are any unassigned cells in the mesh."""
    all_tetra_cell_ids = []
    for cell_set in mesh.cell_sets_dict.keys():
        if "tetra" in mesh.cell_sets_dict[cell_set]:
            all_tetra_cell_ids.extend(mesh.cell_sets_dict[cell_set]["tetra"])

    if any(
        [
            np.setdiff1d(all_tetra_cell_ids, cell_materials[:, 0]).size != 0,
            np.setdiff1d(cell_materials[:, 0], all_tetra_cell_ids).size != 0,
        ]
    ):
        raise SystemValidationError("One or more tetrahedra have unassigned materials!")


def error_message(message: str) -> None:
    """Displays an error message to the user."""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setText("Error")
    msg_box.setInformativeText(message)
    msg_box.setWindowTitle("Error")
    msg_box.exec_()


def generate_elements_data(
    meshes: Mapping[str, Mesh], material_assignments: Mapping[int, MaterialAssignment]
) -> Dict[str, object]:
    """Generates the elements section data for the Solidity input file."""
    node_ids = np.empty((0, 4), dtype="uint64")
    node_id_offset = 0

    cell_materials_sorted = np.empty((0, 2), dtype="uint64")
    cell_id_offset = 0

    total_tetra = sum(
        mesh.cells_dict["tetra"].data.shape[0] for mesh in meshes.values()
    )

    for mesh in meshes.values():
        cell_materials = fetch_material_assignments(mesh, material_assignments)
        check_unassigned_cells(cell_materials, mesh)

        cell_materials_sorted = np.concatenate(
            (
                cell_materials_sorted,
                cell_materials[cell_materials[:, 0].argsort()] + cell_id_offset,
            )
        )
        cell_id_offset += cell_materials.shape[0]

        # We can now get the node ids for each cell, offset by the accumulated number of
        # nodes from previous meshes
        node_ids = np.concatenate((node_ids, mesh.cells_dict["tetra"] + node_id_offset))
        node_id_offset += mesh.points.shape[0]

    return dict(
        num_tetra=total_tetra,
        cell_materials=cell_materials_sorted[:, 1],
        tetra_node_ids=node_ids,
        points_per_tetra=4,
    )


def create_y3d_template() -> str:
    """Creates a Solidity input template using Jinja2."""
    template = env.get_template(config.SOLIDITY_Y3D_TEMPLATE_FILE)

    surface_nodes: Dict[str, np.ndarray] = dict()
    for mesh_name in mesh_datastore:
        gmsh_process = gmsh_process_datastore[mesh_name]
        mesh_surface_nodes = gmsh_process.call_function("get_surface_nodes")
        if not isinstance(mesh_surface_nodes, np.ndarray):
            raise ValueError("Invalid datastructure.")
        surface_nodes[mesh_name] = mesh_surface_nodes

    data: Dict[str, object] = {"num_timesteps": 2000000}
    data.update(generate_elements_data(mesh_datastore, material_assignment_datastore))
    data.update(generate_nodes_data(mesh_datastore, surface_nodes))

    data.update(
        dict(
            materials=material_datastore.values(), num_materials=len(material_datastore)
        )
    )
    return template.render(data)


def generate_y3d_file() -> None:
    """Generates a Solidity input file based on a Jinja2 template."""
    try:
        file_content = create_y3d_template()
        write_file(file_content, config.SOLIDITY_Y3D_FILE_NAME)
    except SystemValidationError as e:
        error_message(e.args[0])
