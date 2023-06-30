"""This module provides functionality to generate an input file for Solidity."""
import logging
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Mapping

import numpy as np
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from meshio import Mesh
from PySide6.QtWidgets import QMessageBox

from .. import config
from .condition import (
    ConditionAssignment,
    ConditionDatastore,
    condition_assignment_datastore,
    condition_datastore,
)
from .gmsh_process import gmsh_process_datastore
from .material import (
    Material,
    MaterialAssignment,
    MaterialDatastore,
    material_assignment_datastore,
    material_datastore,
)
from .meshes import mesh_datastore

env = Environment(
    loader=FileSystemLoader(str(Path(__file__).absolute().parent.parent / "templates")),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
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


def fetch_condition_assignments(
    mesh: Mesh,
    conditions: ConditionDatastore,
    condition_assignment_datastore: Mapping[int, ConditionAssignment],
) -> np.ndarray:
    """Fetch the condition assignments for a given mesh."""
    node_conditions_list = []
    unique_node_ids_mesh = np.array([], dtype="uint64")
    for condition_assignment in condition_assignment_datastore.values():
        if condition_assignment.cell_set_name in mesh.cell_sets_dict:
            for cell_type in mesh.cell_sets_dict[condition_assignment.cell_set_name]:
                cell_id_offset = 0
                if cell_type == "tetra":
                    cell_id_offset = mesh.cells_dict["triangle"].shape[0]
                if cell_type in mesh.cell_sets_dict[condition_assignment.cell_set_name]:
                    cell_ids = (
                        mesh.cell_sets_dict[condition_assignment.cell_set_name][
                            cell_type
                        ]
                        - cell_id_offset
                    )
                    node_ids = mesh.cells_dict[cell_type][cell_ids].flatten()
                    unique_node_ids = np.setdiff1d(
                        np.unique(node_ids), unique_node_ids_mesh
                    )
                    unique_node_ids_mesh = np.concatenate(
                        [unique_node_ids_mesh, unique_node_ids]
                    )
                    condition_id = conditions.get_positional_index(
                        condition_assignment.condition
                    )
                    node_conditions_list.append(
                        np.array(
                            [
                                unique_node_ids,
                                np.full_like(
                                    unique_node_ids,
                                    condition_id,
                                ),
                            ]
                        ).T,
                    )

    if node_conditions_list:
        return np.concatenate(node_conditions_list)

    return np.empty((0, 2), dtype="uint64")


def check_unassigned_nodes(node_conditions: np.ndarray, mesh: Mesh) -> None:
    """Checks if there are any unassigned cells in the mesh."""
    node_ids = np.arange(mesh.points.shape[0], dtype="uint64")

    if any(
        [
            np.setdiff1d(node_ids, node_conditions[:, 0]).size != 0,
            np.setdiff1d(node_conditions[:, 0], node_ids).size != 0,
        ]
    ):
        raise SystemValidationError("One or more nodes have unassigned conditions!")


def generate_nodes_data(
    meshes: Mapping[str, Mesh],
    surface_nodes: Mapping[str, np.ndarray],
    conditions: ConditionDatastore,
    condition_assignment_datastore: Mapping[int, ConditionAssignment],
) -> Dict[str, Any]:
    """Prepare data needed for template renderering."""
    num_nodes = sum(mesh.points.shape[0] for mesh in meshes.values())
    all_nodes = np.concatenate([mesh.points for mesh in meshes.values()], axis=0)

    combined_surface_nodes = np.array([])
    incr = 0
    node_conditions_sorted = np.empty((0, 2), dtype="uint64")
    for mesh_name in meshes:
        mesh_surface_nodes = surface_nodes[mesh_name]
        mesh_surface_nodes = mesh_surface_nodes + incr
        combined_surface_nodes = np.concatenate(
            [combined_surface_nodes, mesh_surface_nodes]
        )

        node_conditions = fetch_condition_assignments(
            meshes[mesh_name], conditions, condition_assignment_datastore
        )
        check_unassigned_nodes(node_conditions, meshes[mesh_name])

        node_conditions_sorted = np.concatenate(
            (
                node_conditions_sorted,
                node_conditions[node_conditions[:, 0].argsort()] + incr,
            )
        )

        incr += meshes[mesh_name].points.shape[0]

    surface_node_flags = np.zeros((num_nodes,), dtype="uint64")
    surface_node_flags[combined_surface_nodes.astype("uint64")] = 1

    return dict(
        num_nodes=num_nodes,
        nodes=all_nodes,
        surface_node_flags=surface_node_flags,
        node_conditions=node_conditions_sorted[:, 1],
    )


def fetch_material_assignments(
    mesh: Mesh,
    materials: MaterialDatastore,
    material_assignments: Mapping[int, MaterialAssignment],
) -> np.ndarray:
    """Fetches the material assignments for a given mesh."""
    cell_materials_list = []
    for assignment in material_assignments.values():
        if assignment.cell_set_name in mesh.cell_sets_dict:
            cell_ids = mesh.cell_sets_dict[assignment.cell_set_name]["tetra"]
            material_id = materials.get_positional_index(assignment.material)
            cell_materials_list.append(
                np.array(
                    [
                        cell_ids,
                        np.full_like(cell_ids, material_id),
                    ]
                ).T
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
    meshes: Mapping[str, Mesh],
    material_assignments: Mapping[int, MaterialAssignment],
    surface_nodes: Mapping[str, np.ndarray],
) -> Dict[str, object]:
    """Generates the elements section data for the Solidity input file."""
    points_per_tetra = 4
    all_node_ids = np.empty((0, points_per_tetra + 1), dtype="uint64")
    boundary_tetra = np.empty((0,), dtype="uint64")

    node_id_offset = 0

    cell_materials_sorted = np.empty((0, 2), dtype="uint64")
    cell_id_offset = 0

    total_tetra = sum(
        mesh.cells_dict["tetra"].data.shape[0] for mesh in meshes.values()
    )

    for i, mesh_name in enumerate(meshes):
        cell_materials = fetch_material_assignments(
            meshes[mesh_name], material_assignments
        )
        check_unassigned_cells(cell_materials, meshes[mesh_name])

        cell_materials_sorted = np.concatenate(
            (
                cell_materials_sorted,
                cell_materials[cell_materials[:, 0].argsort()] + cell_id_offset,
            )
        )
        cell_id_offset += cell_materials.shape[0]

        # We can now get the node ids for each cell, offset by the accumulated number of
        # nodes from previous meshes
        node_ids = meshes[mesh_name].cells_dict["tetra"] + node_id_offset
        # Append the mesh ID to each row
        mesh_ids = np.full(
            (meshes[mesh_name].cells_dict["tetra"].shape[0], 1), i + 1, dtype="uint64"
        )
        node_ids = np.concatenate((node_ids, mesh_ids), axis=1)

        all_node_ids = np.concatenate((all_node_ids, node_ids), axis=0)

        # Find the indices of tetra elements that contain surface nodes
        indices = np.where(
            np.apply_along_axis(
                lambda x: np.isin(x[:4], surface_nodes[mesh_name]).any(),
                1,
                node_ids,
            )
        )[0]
        boundary_tetra_layer = np.zeros(node_ids.shape[0], dtype="uint64")
        np.put(boundary_tetra_layer, indices, i + 1)
        boundary_tetra = np.concatenate(
            (
                (
                    boundary_tetra,
                    boundary_tetra_layer,
                )
            )
        )

        node_id_offset += meshes[mesh_name].points.shape[0]

    return dict(
        num_tetra=total_tetra,
        points_per_tetra=points_per_tetra,
        cell_materials=cell_materials_sorted[:, 1],
        tetra_node_ids=all_node_ids,
        boundary_tetra=boundary_tetra,
    )


def generate_material_data(materials: Mapping[int, Material]) -> Dict[str, Any]:
    """Generates data for the material properties section of the input file."""
    property_lines: Dict[str, Any] = {}
    for material in materials.values():
        for property_label, property_ in material.properties.items():
            property_line_dict = property_lines.setdefault(property_label, {})
            property_data = (
                property_.data if property_.enabled else property_.default_data
            )
            if property_data is None:
                raise SystemValidationError(
                    "Has not been set for the property '{property_.name}' of material "
                    "'{material.name}'."
                )
            for key, value in property_data.items():
                property_line_dict.setdefault(key, []).append(value)
        calculated_properties = property_lines.setdefault("_calculated", {})
        calculated_properties.setdefault("is_joint", []).append(13)
        calculated_properties.setdefault("is_fracture", []).append(
            3 if material.properties["fracture"].enabled else 0
        )

    # add in additional copies of materials with joint elements
    extra_materials = 0
    for i, material in enumerate(materials.values()):
        if not material.properties["fracture"].enabled:
            continue
        extra_materials += 1
        for property_label, property_ in material.properties.items():
            property_line_dict = property_lines[property_label]
            for property_line in property_line_dict.values():
                property_line.append(property_line[i])
        property_lines["_calculated"]["is_joint"].append(15)
        property_lines["_calculated"]["is_fracture"].append(0)
    return dict(
        materials=materials.values(),
        num_materials=len(materials) + extra_materials,
        material_properties=property_lines,
    )


def get_tetra_side_lengths(meshes: Mapping[str, Mesh]) -> np.ndarray:
    """Gets the side lengths of the tetrahedra in the mesh."""
    # this is only good for linear meshes
    # it is probably too memory/compute intensive for large meshes
    # gmsh will release a built in way to do this in the 4.12 release
    # https://gitlab.onelab.info/gmsh/gmsh/-/blob/0dacd204c5b936efdfb9341fd71cabbb06ebb9e2/api/gmsh.py#L2989

    lengths = np.array([])
    for mesh in meshes.values():
        pairings = np.empty((0, 2), dtype="uint64")
        for cell in mesh.cells_dict["tetra"]:
            edges = np.array(list(combinations(cell, 2)))
            pairings = np.concatenate([pairings, edges], axis=0)

        pairings = np.unique(pairings, axis=0)

        dist_vectors = mesh.points[pairings[:, 0]] - mesh.points[pairings[:, 1]]
        lengths = np.concatenate((lengths, np.linalg.norm(dist_vectors, axis=1)))
    return lengths


def generate_interactions_data(meshes: Mapping[str, Mesh]) -> Dict[str, Any]:
    """Generates the interactions section data for the Solidity input file."""
    tetra_side_lengths = get_tetra_side_lengths(meshes)

    min_length = np.min(tetra_side_lengths)
    mean_length = np.mean(tetra_side_lengths)

    return dict(mean_length=mean_length, min_length=min_length)


def generate_surface_elements_data(meshes: Mapping[str, Mesh]) -> Dict[str, Any]:
    """Generates the surface elements section data for the Solidity input file."""
    points_per_triangle = 3
    node_ids = np.empty((0, 3), dtype="uint64")
    node_id_offset = 0

    total_triangles = sum(
        mesh.cells_dict["triangle"].data.shape[0] for mesh in meshes.values()
    )

    for mesh in meshes.values():
        node_ids = np.concatenate(
            (node_ids, mesh.cells_dict["triangle"] + node_id_offset)
        )
        node_id_offset += mesh.points.shape[0]

    return dict(
        num_triangles=total_triangles,
        points_per_triangle=points_per_triangle,
        triangle_node_ids=node_ids,
    )


def create_y3d_template() -> str:
    """Creates a Solidity input template using Jinja2."""
    template = env.get_template(config.SOLIDITY_Y3D_TEMPLATE_FILE)
    logging.info(f"Generating Y3D file from {template.filename}")

    surface_nodes: Dict[str, np.ndarray] = dict()
    for mesh_name in mesh_datastore:
        gmsh_process = gmsh_process_datastore[mesh_name]
        mesh_surface_nodes = gmsh_process.call_function("get_surface_nodes")
        if not isinstance(mesh_surface_nodes, np.ndarray):
            raise ValueError("Invalid datastructure.")
        surface_nodes[mesh_name] = mesh_surface_nodes

    data: Dict[str, object] = {"num_timesteps": 2000000}
    data.update(
        generate_elements_data(
            mesh_datastore, material_assignment_datastore, surface_nodes
        )
    )
    data.update(generate_interactions_data(mesh_datastore))
    data.update(
        generate_nodes_data(
            mesh_datastore,
            surface_nodes,
            condition_datastore,
            condition_assignment_datastore,
        )
    )
    data.update(generate_material_data(material_datastore))
    data.update(
        dict(
            conditions=condition_datastore.values(),
            num_conditions=len(condition_datastore),
        )
    )
    data.update(generate_surface_elements_data(mesh_datastore))
    return template.render(data)


def generate_y3d_file() -> None:
    """Generates a Solidity input file based on a Jinja2 template."""
    try:
        file_content = create_y3d_template()
        write_file(file_content, config.SOLIDITY_Y3D_FILE_NAME)
    except SystemValidationError as e:
        error_message(e.args[0])
