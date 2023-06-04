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

    for mesh in mesh_datastore.values():
        cell_materials_list = []
        all_cells = mesh.cells
        all_cell_sets = mesh.cell_sets
        all_tetra_cells_get = mesh.get_cells_type("tetra")
        all_cells_dict = mesh.cells_dict
        all_cell_sets_dict = mesh.cell_sets_dict
        cells_surface = mesh.cell_sets_dict["ball1_surface_0"]
        cells_volume = mesh.cell_sets_dict["ball1_volume"]
        for assignment in material_assignment_datastore.values():
            cell_ids = mesh.cell_sets_dict[assignment.cell_set_name]["tetra"]
            cell_materials_list.append(
                np.array([cell_ids, np.full_like(cell_ids, assignment.material_id)]).T
            )
        if cell_materials_list:
            cell_materials = np.concatenate(cell_materials_list, axis=0)
        # We need to add to cell_materials all the cells that are not assigned to any material
        all_tetra_cells = mesh.cells_dict["tetra"]
        tetra_cells_not_assigned = np.setdiff1d(all_tetra_cells, cell_materials[:, 0])
        # Now we have a list of unassigned cells, we can give them a material value = -1
        # and concatenate them to the cell_materials array
        cell_materials = np.concatenate(
            [
                cell_materials,
                np.array(
                    [
                        tetra_cells_not_assigned,
                        np.full_like(tetra_cells_not_assigned, -1),
                    ]
                ).T,
            ],
            axis=0,
        )
        np.set_printoptions(threshold=np.inf)
        cell_materials_sorted = cell_materials[cell_materials[:, 0].argsort()]

        print(cell_materials_sorted)

    data = {
        "num_timesteps": 2000000,
        "melem": total_tetra + 1,
        "nelem": total_tetra,
        "melno": points_per_tetra + 1,
        "nelno": points_per_tetra,
        # "elemsMat": tetra_cells_material_index,
        # "elemsConec": elemsConec,
    }

    return template.render(data)


def generate_y3d_file() -> None:
    """Generates a Solidity input file based on a Jinja2 template."""
    file_content = create_y3d_template()
    write_file(file_content, config.SOLIDITY_Y3D_FILE_NAME)
