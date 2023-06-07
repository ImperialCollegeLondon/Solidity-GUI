"""This module provides functionality to generate an input file for Solidity."""
from pathlib import Path

import numpy as np
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .. import config
from .geometry import mesh_generator_datastore
from .meshes import mesh_datastore

env = Environment(
    loader=FileSystemLoader(str(Path(__file__).absolute().parent.parent / "templates")),
    undefined=StrictUndefined,
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

    meshes = list(mesh_datastore.values())
    num_nodes = sum(mesh.points.shape[0] for mesh in meshes)

    all_nodes = np.concatenate([mesh.points for mesh in meshes], axis=0)

    all_surface_nodes = np.array([])
    incr = 0
    for mesh, mesh_generator in zip(meshes, mesh_generator_datastore.values()):
        surface_nodes = mesh_generator.get_surface_nodes() + incr
        all_surface_nodes = np.concatenate([all_surface_nodes, surface_nodes])
        incr += mesh.points.shape[0]

    surface_node_flags = np.zeros((num_nodes,), dtype="uint64")
    surface_node_flags[all_surface_nodes.astype("uint64")] = 1

    data = dict(
        num_timesteps=2000000,
        num_nodes=num_nodes,
        nodes=all_nodes,
        surface_node_flags=surface_node_flags,
    )

    return template.render(data)


def generate_y3d_file() -> None:
    """Generates a Solidity input file based on a Jinja2 template."""
    file_content = create_y3d_template()
    write_file(file_content, config.SOLIDITY_Y3D_FILE_NAME)
