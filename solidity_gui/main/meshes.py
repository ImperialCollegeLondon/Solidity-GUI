"""Module for storage of mesh related data."""
from collections.abc import Iterable

import meshio
import numpy as np
from pubsub import pub

from .components import Component
from .datastore import Datastore
from .gmsh_process import GmshProcess, gmsh_process_datastore
from .mesh_sizes import MeshSize

mesh_datastore: Datastore[str, meshio.Mesh] = Datastore("meshes")


def _add_component_to_geometry_begin(mesh_name: str, component: Component) -> None:
    """Add a new geometric component and render and display its rough mesh."""
    try:
        gmsh_process = gmsh_process_datastore[mesh_name]
    except KeyError:
        gmsh_process = GmshProcess(mesh_name)
        gmsh_process.start()
        gmsh_process_datastore[mesh_name] = gmsh_process

    gmsh_process.call_function_async("add_component", component=component)


def _add_component_to_geometry_end(mesh_name: str, obj: meshio.Mesh) -> None:
    """Store and broadcast the resulting mesh after component addition."""
    mesh_datastore[mesh_name] = obj
    pub.sendMessage("geometry.updated", mesh_name=mesh_name, mesh=obj)


def _create_mesh_from_geometry_begin(
    mesh_sizes: Iterable[MeshSize], default_size: float
) -> None:
    """Generate and display a high quality mesh from the current geometry."""
    for gmsh_process in gmsh_process_datastore.values():
        gmsh_process.call_function_async(
            "generate_mesh", mesh_sizes=mesh_sizes, default_size=default_size
        )


def _create_mesh_from_geometry_end(mesh_name: str, obj: meshio.Mesh) -> None:
    """Store and broadcast the resulting mesh after high quality mesh generation."""
    mesh_datastore[mesh_name] = obj
    pub.sendMessage("mesh.updated", mesh_name=mesh_name, mesh=obj)


pub.subscribe(_add_component_to_geometry_begin, "geometry.update")
pub.subscribe(_add_component_to_geometry_end, "add_component.finish")
pub.subscribe(_create_mesh_from_geometry_begin, "mesh.create")
pub.subscribe(_create_mesh_from_geometry_end, "generate_mesh.finish")


def get_cell_offset(cells_dict: dict[str, np.ndarray], cell_type: str) -> int:
    """Calculate the offset applied to indices of a cell_type for a mesh.

    The indices return by gmsh for cells (elements) are offset by the total number of
    cells of lower dimension present in the mesh. For instance, if a mesh has two
    vertices the indices for lines will start at 2. If the mesh also has 3 lines then
    the indices for triangles will start at 5 and so on. We often want the map from this
    indexing system to one in which each of the cell types are indexed
    independently. The offset value return by this function can be used for this.

    Args:
      cells_dict: the cell data from the mesh
      cell_type: the type of cell for which we want the offset
    """
    offset = 0
    for type_ in ("vertex", "line", "triangle"):
        if cell_type == type_:
            break
        offset += cells_dict[type_].shape[0]
    return offset
