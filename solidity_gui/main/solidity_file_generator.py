"""This module provides functionality to generate an input file for Solidity."""
from pathlib import Path
from typing import List

import numpy as np
from jinja2 import Environment, FileSystemLoader
from meshio import Mesh

from .. import config
from .material import material_assignment_datastore
from .meshes import mesh_datastore

env = Environment(
    loader=FileSystemLoader(str(Path(__file__).absolute().parent.parent / "templates"))
)


def write_file(file_content: str, output_file: Path | str) -> None:
    """Write the contents of file_content to file.

    Raises:
        IOError: If there is a problem writing to the output file.
    """
    with open(output_file, "w") as f:
        f.write(file_content)


def fetch_material_assignments(mesh: Mesh) -> np.ndarray:
    """Fetches the material assignments for a given mesh."""
    cell_materials_list = []
    for assignment in material_assignment_datastore.values():
        cell_ids = mesh.cell_sets_dict[assignment.cell_set_name]["tetra"]
        cell_materials_list.append(
            np.array([cell_ids, np.full_like(cell_ids, assignment.material_id)]).T
        )
    if cell_materials_list:
        cell_materials = np.concatenate(cell_materials_list, axis=0)
    else:
        cell_materials = np.empty((0, 2), dtype=np.uint64)

    return cell_materials


def check_unassigned_cells(cell_materials: np.ndarray, mesh: Mesh) -> bool:
    """Checks if there are any unassigned cells in the mesh."""

    all_tetra_cell_ids = []
    for cell_set in mesh.cell_sets_dict.keys():
        if "tetra" in mesh.cell_sets_dict[cell_set]:
            all_tetra_cell_ids.extend(mesh.cell_sets_dict[cell_set]["tetra"])

    return np.setdiff1d(all_tetra_cell_ids, cell_materials[:, 0]) or np.setdiff1d(
        cell_materials[:, 0], all_tetra_cell_ids
    )


def generate_elements_data() -> tuple[np.ndarray, List[int]]:
    """Generates the elements section data for the Solidity input file."""
    node_ids: List[int] = []
    node_id_offset = 0

    cell_materials_sorted = np.empty((0, 2), dtype=np.uint64)
    cell_id_offset = 0

    for mesh in mesh_datastore.values():
        cell_materials = fetch_material_assignments(mesh)
        if check_unassigned_cells():
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText("Error")
            msg_box.setInformativeText(
                "One or more tetrahedra have unassigned materials!"
            )
            msg_box.setWindowTitle("Error")
            msg_box.exec_()

        cell_materials_sorted = (
            cell_materials[cell_materials[:, 0].argsort()] + cell_id_offset
        )
        cell_id_offset += cell_materials.shape[0]

        # We can now get the node ids for each cell, offset by the accumulated number of
        # nodes from previous meshes
        node_ids.extend(
            node_id + node_id_offset for node_id in mesh.cells_dict["tetra"]
        )

        node_id_offset += mesh.points.shape[0]

    return cell_materials_sorted, node_ids


def create_y3d_template() -> str:
    """Creates a Solidity input template using Jinja2."""
    template = env.get_template(config.SOLIDITY_Y3D_TEMPLATE_FILE)

    total_tetra = sum(
        cell.data.shape[0]
        for value in mesh_datastore.values()
        for cell in value.cells
        if cell.type == "tetra"
    )

    for mesh in mesh_datastore.values():
        for tetra_cell in mesh.cells:
            if tetra_cell.type == "tetra":
                points_per_tetra = tetra_cell.data[0].size
                break

    cell_materials_sorted, node_ids = generate_elements_data()

    data = {
        "num_timesteps": 2000000,
        "melem": total_tetra + 1,
        "nelem": total_tetra,
        "melno": points_per_tetra + 1,
        "nelno": points_per_tetra,
        "elemsMat": cell_materials_sorted[:, 1],
        "elemsConec": node_ids,
    }

    return template.render(data)


def generate_y3d_file() -> None:
    """Generates a Solidity input file based on a Jinja2 template."""
    file_content = create_y3d_template()
    write_file(file_content, config.SOLIDITY_Y3D_FILE_NAME)
