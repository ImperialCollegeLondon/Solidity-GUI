"""This module provides functionality to generate an input file for Solidity."""
from pathlib import Path
from typing import Any, Dict, Mapping

import numpy as np
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from meshio import Mesh

from .. import config
from .gmsh_process import gmsh_process_datastore
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


def get_template_data(
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
        num_timesteps=2000000,
        num_nodes=num_nodes,
        nodes=all_nodes,
        surface_node_flags=surface_node_flags,
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

    data = get_template_data(mesh_datastore, surface_nodes)
    return template.render(data)


def generate_y3d_file() -> None:
    """Generates a Solidity input file based on a Jinja2 template."""
    file_content = create_y3d_template()
    write_file(file_content, config.SOLIDITY_Y3D_FILE_NAME)
