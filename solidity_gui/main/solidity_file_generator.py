"""This module provides functionality to generate an input file for Solidity."""
from pathlib import Path

import numpy as np
from jinja2 import Environment, FileSystemLoader

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

    node_ids = []
    node_id_offset = 0

    for mesh in mesh_datastore.values():
        cell_materials_list = []
        for assignment in material_assignment_datastore.values():
            cell_ids = mesh.cell_sets_dict[assignment.cell_set_name]["tetra"]
            cell_materials_list.append(
                np.array([cell_ids, np.full_like(cell_ids, assignment.material_id)]).T
            )
        if cell_materials_list:
            cell_materials = np.concatenate(cell_materials_list, axis=0)
        else:
            cell_materials = np.empty((0, 2), dtype=int)

        # We need to add to cell_materials all the cells that are not assigned to any
        # material. We can give them a material value = -1
        # First lets get a list of all the tetra cell IDs. There may be a more elegant
        # way of doing this
        all_tetra_cell_ids = []
        for cell_set in mesh.cell_sets_dict.keys():
            if "tetra" in mesh.cell_sets_dict[cell_set]:
                all_tetra_cell_ids.extend(mesh.cell_sets_dict[cell_set]["tetra"])

        # We can diff the all_tetra_cell_ids list with list of assigned cell ids to get
        # all the unassigned tetra cell ids
        tetra_cells_not_assigned = np.setdiff1d(
            all_tetra_cell_ids, cell_materials[:, 0]
        )
        cell_materials = np.concatenate(
            [
                cell_materials,
                np.array(
                    [
                        tetra_cells_not_assigned,
                        np.full_like(tetra_cells_not_assigned, -1, dtype=int),
                    ]
                ).T,
            ],
            axis=0,
        )

        cell_materials_sorted = cell_materials[cell_materials[:, 0].argsort()]

        # We can now get the node ids for each cell, offset by the accumulated number of
        # nodes from previous meshes
        node_ids.extend(
            node_id + node_id_offset for node_id in mesh.cells_dict["tetra"]
        )

        node_id_offset += mesh.points.shape[0]

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
