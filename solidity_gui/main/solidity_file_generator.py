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

    # This dictionary will contain the cell set names and the corresponding cell set ids
    # These ids are used in the I2ELTO section of the input file
    cell_set_ids = {}
    for mesh in mesh_datastore.values():
        for id, (cell_set_name, cell_set) in enumerate(mesh.cell_sets.items()):
            cell_set_ids[cell_set_name] = id

    # This list is populated with the material index assigned to each tetra cell
    tetra_cells_material_index = []
    # This list is populated with the cell set ids assigned to each tetra cell
    tetra_cell_part_ids = []
    tetra_cells_node_ids = []
    for mesh in mesh_datastore.values():
        tetra_cells = mesh.cells_dict["tetra"]
        for tetra_cell in tetra_cells:
            tetra_cells_node_ids.append(tetra_cell)
            material_id = -1
            tetra_cell_part_id = -1
            for cell_set_name, cell_set in mesh.cell_sets.items():
                if cell_set[2] is not None and all(
                    vertex in cell_set[2] for vertex in tetra_cell
                ):
                    tetra_cell_part_id = cell_set_ids[cell_set_name]
                    tetra_cell_set_name = cell_set_name
                    for assignment in material_assignment_datastore.values():
                        if tetra_cell_set_name == assignment.cell_set_name:
                            material_id = assignment.material_id
                            break
            tetra_cells_material_index.append(material_id)
            tetra_cell_part_ids.append(tetra_cell_part_id)

    # It's easier to join the two lists here than in the template
    elemsConec = [
        np.append(tetra_cells_node_ids[i], tetra_cell_part_ids[i])
        for i in range(len(tetra_cells_node_ids))
    ]

    data = {
        "num_timesteps": 2000000,
        "melem": total_tetra + 1,
        "nelem": total_tetra,
        "melno": points_per_tetra + 1,
        "nelno": points_per_tetra,
        "elemsMat": tetra_cells_material_index,
        "elemsConec": elemsConec,
    }

    return template.render(data)


def generate_y3d_file() -> None:
    """Generates a Solidity input file based on a Jinja2 template."""
    file_content = create_y3d_template()
    write_file(file_content, config.SOLIDITY_Y3D_FILE_NAME)
