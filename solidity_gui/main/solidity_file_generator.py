"""This module provides functionality to generate an input file for Solidity."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from .material import material_assignment_datastore
from .meshes import mesh_datastore
from .. import config

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
        for cell in mesh.cells:
            if cell.type == "tetra":
                points_per_tetra = cell.data[0].size
                break

    # We want to popoulate this list with the material index assigned to each tetra cell
    tetra_cells_material_index = []
    for mesh in mesh_datastore.values():
        for assignment in material_assignment_datastore.values():
            subset_mesh = mesh.subset(assignment.cell_set_name, cell_type="tetra")
            # cell_set = mesh.cell_sets.get(assignment.cell_set_name)
            print(subset_mesh)
            # tetra_indices = cell_set["tetra"]
            for cell in subset_mesh:
                tetra_cells_material_index.append(assignment.material_index)

    data = {
        "num_timesteps": 2000000,
        "melem": total_tetra + 1,
        "nelem": total_tetra,
        "melno": points_per_tetra + 1,
        "nelno": points_per_tetra,
    }

    return template.render(data)


def generate_y3d_file() -> None:
    """Generates a Solidity input file based on a Jinja2 template."""
    file_content = create_y3d_template()
    write_file(file_content, config.SOLIDITY_Y3D_FILE_NAME)
