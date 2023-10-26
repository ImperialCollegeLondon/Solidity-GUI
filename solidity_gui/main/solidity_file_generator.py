"""This module provides functionality to generate an input file for Solidity."""
import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from meshio import Mesh
from typing_extensions import TypedDict

from .. import config
from .condition import (
    ConditionAssignmentDatastore,
    ConditionDatastore,
    condition_assignment_datastore,
    condition_datastore,
)
from .control import control_datastore
from .error_message import display_error_message
from .gmsh_process import gmsh_process_datastore
from .initial_condition import (
    InitialConditionAssignmentDatastore,
    InitialConditionDatastore,
    initial_condition_assignment_datastore,
    initial_condition_datastore,
)
from .material import (
    JointMaterialDatastore,
    Material,
    MaterialAssignment,
    MaterialDatastore,
    get_joint_material_interfaces,
    joint_material_datastore,
    material_assignment_datastore,
    material_datastore,
)
from .meshes import get_cell_offset, mesh_datastore

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
    condition_assignments: ConditionAssignmentDatastore,
) -> np.ndarray:
    """Fetch the condition assignments for a given mesh."""
    node_count = mesh.points.shape[0]
    node_assignments = np.array(
        (np.arange(node_count), np.full(node_count, -1)), dtype="int64"
    ).T
    # important that we work on the cell types in this order so that lower dimension
    # entities take precedence over higher dimension
    cell_type_order = ("tetra", "triangle")
    mesh_assignments = condition_assignments.get_assignments_for_mesh(mesh)
    for cell_type in cell_type_order:
        if cell_type not in mesh_assignments:
            continue
        for assignment in mesh_assignments[cell_type]:
            cell_set = mesh.cell_sets_dict[assignment.cell_set_name][cell_type]
            cell_id_offset = get_cell_offset(mesh.cells_dict, cell_type)
            cell_ids = cell_set - cell_id_offset
            node_ids = np.unique(mesh.cells_dict[cell_type][cell_ids].flatten())
            condition_id = conditions.get_positional_index(assignment.condition)
            node_assignments[node_ids, 1] = condition_id
    return node_assignments


def fetch_initial_conditions(
    mesh: Mesh,
    initial_conditions: InitialConditionDatastore,
    initial_condition_assignments: InitialConditionAssignmentDatastore,
) -> np.ndarray:
    """Fetch the initial condition data applied to the nodes of a mesh.

    Args:
      mesh: the mesh of interest
      initial_conditions: datastore containing initial condition data
      initial_condition_assignments: datastore associating initial conditions with mesh
    """
    node_initial_conditions = np.zeros_like(mesh.points)
    mesh_assignments = initial_condition_assignments.get_assignments_for_mesh(mesh)
    for assignment in mesh_assignments:
        cell_set = mesh.cell_sets_dict[assignment.cell_set_name]["tetra"]
        cell_ids = cell_set - get_cell_offset(mesh.cells_dict, "tetra")
        node_ids = np.unique(mesh.cells_dict["tetra"][cell_ids].flatten())
        properties = assignment.initial_condition.properties
        node_initial_conditions[node_ids] = np.array(
            [properties["x"], properties["y"], properties["z"]]
        )
    return node_initial_conditions


def check_unassigned_nodes(node_conditions: np.ndarray, mesh: Mesh) -> None:
    """Checks if there are any unassigned cells in the mesh."""
    if any(node_conditions[:, 1] == -1):
        raise SystemValidationError("One or more nodes have unassigned conditions!")


def generate_nodes_data(
    meshes: Mapping[str, Mesh],
    surface_nodes: Mapping[str, np.ndarray],
    conditions: ConditionDatastore,
    condition_assignments: ConditionAssignmentDatastore,
    initial_conditions: InitialConditionDatastore,
    initial_condition_assignments: InitialConditionAssignmentDatastore,
) -> dict[str, object]:
    """Prepare data needed for template renderering."""
    num_nodes = sum(mesh.points.shape[0] for mesh in meshes.values())
    all_nodes = np.concatenate([mesh.points for mesh in meshes.values()], axis=0)

    combined_surface_nodes = np.array([])
    incr = 0
    all_node_conditions = np.empty((0, 2), dtype="int64")
    all_node_initial_conditions = np.empty((0, 3))
    for mesh_name in meshes:
        mesh_surface_nodes = surface_nodes[mesh_name]
        mesh_surface_nodes = mesh_surface_nodes + incr
        combined_surface_nodes = np.concatenate(
            [combined_surface_nodes, mesh_surface_nodes]
        )

        mesh_node_conditions = fetch_condition_assignments(
            meshes[mesh_name], conditions, condition_assignments
        )
        check_unassigned_nodes(mesh_node_conditions, meshes[mesh_name])

        mesh_node_conditions[:, 0] += incr
        all_node_conditions = np.concatenate(
            (all_node_conditions, mesh_node_conditions)
        )

        mesh_node_initial_conditions = fetch_initial_conditions(
            meshes[mesh_name], initial_conditions, initial_condition_assignments
        )
        all_node_initial_conditions = np.concatenate(
            (all_node_initial_conditions, mesh_node_initial_conditions)
        )

        incr += meshes[mesh_name].points.shape[0]

    surface_node_flags = np.zeros((num_nodes,), dtype="uint64")
    surface_node_flags[combined_surface_nodes.astype("uint64")] = 1

    return dict(
        num_nodes=num_nodes,
        nodes=all_nodes,
        surface_node_flags=surface_node_flags,
        node_conditions=all_node_conditions[:, 1],
        node_initial_conditions=all_node_initial_conditions,
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


class ElementData(TypedDict):
    """Typed dict class providing types for element data."""

    num_tetra: int
    points_per_tetra: int
    cell_materials: np.ndarray
    tetra_node_ids: np.ndarray
    boundary_tetra: np.ndarray
    num_meshes: int


def generate_elements_data(
    meshes: Mapping[str, Mesh],
    materials: MaterialDatastore,
    material_assignments: Mapping[int, MaterialAssignment],
    surface_nodes: Mapping[str, np.ndarray],
) -> ElementData:
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

    for i, (mesh_name, mesh) in enumerate(meshes.items()):
        cell_materials = fetch_material_assignments(
            mesh, materials, material_assignments
        )
        check_unassigned_cells(cell_materials, mesh)

        cell_materials[:, 0] += cell_id_offset

        cell_materials_sorted = np.concatenate(
            (
                cell_materials_sorted,
                cell_materials[cell_materials[:, 0].argsort()],
            )
        )
        cell_id_offset += cell_materials.shape[0]

        # We can now get the node ids for each cell, offset by the accumulated number of
        # nodes from previous meshes
        node_ids = mesh.cells_dict["tetra"]

        # Find the indices of tetra elements that contain surface nodes
        indices = np.where(
            np.apply_along_axis(
                lambda x: np.isin(x[:4], surface_nodes[mesh_name]).any(),
                1,
                node_ids,
            )
        )[0]
        boundary_tetra_layer = np.zeros(node_ids.shape[0], dtype="uint64")
        boundary_tetra_layer[indices] = i + 1
        boundary_tetra = np.concatenate(
            (
                boundary_tetra,
                boundary_tetra_layer,
            )
        )

        # Append the mesh ID to each row
        mesh_ids = np.full(
            (mesh.cells_dict["tetra"].shape[0], 1), i + 1, dtype="uint64"
        )
        node_ids = np.concatenate((node_ids + node_id_offset, mesh_ids), axis=1)

        all_node_ids = np.concatenate((all_node_ids, node_ids), axis=0)

        node_id_offset += mesh.points.shape[0]

    return dict(
        num_tetra=total_tetra,
        points_per_tetra=points_per_tetra,
        cell_materials=cell_materials_sorted[:, 1],
        tetra_node_ids=all_node_ids,
        boundary_tetra=boundary_tetra,
        num_meshes=len(meshes),
    )


def generate_material_data(materials: Mapping[int, Material]) -> dict[str, Any]:
    """Generates data for the material properties section of the input file."""
    property_lines: dict[str, Any] = {}
    for i, material in enumerate(materials.values(), 1):
        for property_label, property_ in material.properties.items():
            property_line_dict = property_lines.setdefault(property_label, {})
            property_data = (
                property_.data if property_.enabled else property_.default_data
            )
            if property_data is None:
                raise SystemValidationError(
                    f"Has not been set for the property '{property_.name}' of material "
                    f"'{material.name}'."
                )
            for key, value in property_data.items():
                property_line_dict.setdefault(key, []).append(value)
        calculated_properties = property_lines.setdefault("_calculated", {})
        calculated_properties.setdefault("is_joint", []).append(13)
        calculated_properties.setdefault("is_fracture", []).append(
            3 if material.properties["joint"].enabled else 0
        )
        calculated_properties.setdefault("material_index", []).append(i)

    # add in additional copies of materials with joint elements
    extra_materials = 0
    for i, material in enumerate(materials.values()):
        if not material.properties["joint"].enabled:
            continue
        extra_materials += 1
        for property_label, property_ in material.properties.items():
            property_line_dict = property_lines[property_label]
            for property_line in property_line_dict.values():
                property_line.append(property_line[i])
        property_lines["_calculated"]["is_joint"].append(15)
        property_lines["_calculated"]["is_fracture"].append(0)
        property_lines["_calculated"]["material_index"].append(i + 1)
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


def generate_interactions_data(meshes: Mapping[str, Mesh]) -> dict[str, Any]:
    """Generates the interactions section data for the Solidity input file."""
    tetra_side_lengths = get_tetra_side_lengths(meshes)

    min_length = np.min(tetra_side_lengths)
    mean_length = np.mean(tetra_side_lengths)

    return dict(mean_length=mean_length, min_length=min_length)


class SurfaceElementData(TypedDict):
    """Typed dict class providing types for surface element data."""

    num_triangles: int
    points_per_triangle: int
    triangle_node_ids: np.ndarray


def generate_surface_elements_data(meshes: Mapping[str, Mesh]) -> SurfaceElementData:
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


def get_template_data(
    meshes: Mapping[str, Mesh],
    materials: MaterialDatastore,
    material_assignments: Mapping[int, MaterialAssignment],
    conditions: ConditionDatastore,
    condition_assignments: ConditionAssignmentDatastore,
    initial_conditions: InitialConditionDatastore,
    initial_condition_assignments: InitialConditionAssignmentDatastore,
    control_parameters: Mapping[str, object],
    surface_nodes: Mapping[str, np.ndarray],
) -> dict[str, object]:
    """Get the data needed to render the input file template."""
    data: dict[str, object] = {}
    element_data = generate_elements_data(
        meshes, materials, material_assignments, surface_nodes
    )
    data.update(element_data)
    data.update(generate_interactions_data(meshes))
    data.update(
        generate_nodes_data(
            meshes,
            surface_nodes,
            conditions,
            condition_assignments,
            initial_conditions,
            initial_condition_assignments,
        )
    )
    data.update(generate_material_data(materials))
    data.update(
        dict(
            conditions=conditions.values(),
            num_conditions=len(conditions),
        )
    )
    surface_element_data = generate_surface_elements_data(meshes)
    data.update(surface_element_data)
    num_triangles = surface_element_data["num_triangles"]
    num_joint_elements = (
        ((element_data["num_tetra"] * 4) - num_triangles) // 2
    ) + num_triangles
    data.update(dict(num_joint_elements=num_joint_elements))
    data.update(control_parameters)
    return data


def create_y3d_template() -> str:
    """Creates a Solidity input template using Jinja2."""
    template = env.get_template(config.SOLIDITY_Y3D_TEMPLATE_FILE)
    logging.info(f"Generating Y3D file from {template.filename}")

    surface_nodes: dict[str, np.ndarray] = dict()
    for mesh_name in mesh_datastore:
        gmsh_process = gmsh_process_datastore[mesh_name]
        mesh_surface_nodes = gmsh_process.call_function("get_surface_nodes")
        if not isinstance(mesh_surface_nodes, np.ndarray):
            raise ValueError("Invalid datastructure.")
        surface_nodes[mesh_name] = mesh_surface_nodes

    data = get_template_data(
        mesh_datastore,
        material_datastore,
        material_assignment_datastore,
        condition_datastore,
        condition_assignment_datastore,
        initial_condition_datastore,
        initial_condition_assignment_datastore,
        control_datastore,
        surface_nodes,
    )
    return template.render(data)


def generate_y3d_file() -> None:
    """Generates a Solidity input file based on a Jinja2 template."""
    file_content = create_y3d_template()
    write_file(file_content, config.SOLIDITY_Y3D_FILE_NAME)


@dataclass
class JointMaterialData:
    """Dataclass holding joint material data for rendering by Jinja2."""

    index1: int
    index2: int
    data: dict[str, object]


def get_mat_data(
    joint_material_interfaces: Iterable[tuple[Material, Material]],
    joint_materials: JointMaterialDatastore,
    materials: MaterialDatastore,
) -> dict[str, object]:
    """Get the data needed to render the mat file template."""
    joint_material_data: list[JointMaterialData] = []
    for material_id, material in enumerate(materials.values()):
        if material.properties["joint"].enabled:
            other = material.properties["joint"]
            other_data = other.data if other.enabled else other.default_data
            if other_data is None:
                raise SystemValidationError(
                    f"Values have not been set for the property 'other' of "
                    f"material '{material.name}'."
                )
            joint_material_data.append(
                JointMaterialData(
                    index1=material_id,
                    index2=material_id,
                    data=dict(
                        tensile_strength=other_data["tensile_strength"],
                        internal_friction_coefficient=other_data[
                            "internal_friction_coefficient"
                        ],
                        cohesion=other_data["cohesion"],
                        energy_release_rate_mode_1=other_data[
                            "energy_release_rate_mode_1"
                        ],
                        energy_release_rate_mode_2=other_data[
                            "energy_release_rate_mode_2"
                        ],
                    ),
                )
            )
    for material1, material2 in joint_material_interfaces:
        try:
            joint_properties = joint_materials.get_by_materials(
                material1, material2
            ).properties
        except ValueError:
            raise SystemValidationError(
                "Joint material properties have not been set for the interface between "
                f"the materials '{material1.name}' and '{material2.name}'"
            )
        joint_material_data.append(
            JointMaterialData(
                index1=materials.get_positional_index(material1),
                index2=materials.get_positional_index(material2),
                data=joint_properties,
            )
        )
    return dict(
        num_materials=len(joint_material_data), joint_materials=joint_material_data
    )


def create_mat_template() -> str:
    """Render file contents for a Solidity mat file using Jinja2."""
    template = env.get_template(config.SOLIDITY_MAT_TEMPLATE_FILE)
    logging.info(f"Generating Y3D file from {template.filename}")
    joint_material_interfaces = get_joint_material_interfaces(
        gmsh_process_datastore, material_assignment_datastore
    )
    data = get_mat_data(
        joint_material_interfaces,
        joint_material_datastore,
        material_datastore,
    )
    return template.render(data)


def generate_mat_file() -> None:
    """Generates a Solidity mat file from a Jinja2 template."""
    file_content = create_mat_template()
    write_file(file_content, config.SOLIDITY_MAT_FILE_NAME)


def generate_output_files() -> None:
    """Generate all output files and write them to disk."""
    try:
        generate_y3d_file()
        generate_mat_file()
    except SystemValidationError as e:
        display_error_message(e.args[0])
