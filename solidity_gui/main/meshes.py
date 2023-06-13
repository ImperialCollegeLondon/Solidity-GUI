"""Module for storage of mesh related data."""
import meshio
from pubsub import pub

from .datastore import Datastore
from .geometry import Component
from .gmsh_process import GmshProcess, gmsh_process_datastore

mesh_datastore: Datastore[str, meshio.Mesh] = Datastore("meshes")


current_mesh = "default"
DEFAULT_RESOLUTION = 0.1


def _add_component_to_geometry_begin(component: Component) -> None:
    """Add a new geometric component and render and display its rough mesh."""
    try:
        gmsh_process = gmsh_process_datastore[current_mesh]
    except KeyError:
        gmsh_process = GmshProcess()
        gmsh_process.start()
        gmsh_process_datastore[current_mesh] = gmsh_process

    gmsh_process.call_function_async(
        "add_component", component=component, resolution=DEFAULT_RESOLUTION
    )


def _add_component_to_geometry_end(obj: meshio.Mesh) -> None:
    """Store and broadcast the resulting mesh after component addition."""
    mesh_datastore[current_mesh] = obj
    pub.sendMessage("geometry.updated", mesh=obj)


def _create_mesh_from_geometry_begin(size: float) -> None:
    """Generate and display a high quality mesh from the current geometry."""
    gmsh_process = gmsh_process_datastore[current_mesh]
    gmsh_process.call_function_async("generate_mesh", resolution=size)


def _create_mesh_from_geometry_end(obj: meshio.Mesh) -> None:
    """Store and broadcast the resulting mesh after high quality mesh generation."""
    mesh_datastore[current_mesh] = obj
    pub.sendMessage("mesh.updated", mesh=obj)


pub.subscribe(_add_component_to_geometry_begin, "geometry.update")
pub.subscribe(_add_component_to_geometry_end, "add_component.finish")
pub.subscribe(_create_mesh_from_geometry_begin, "mesh.create")
pub.subscribe(_create_mesh_from_geometry_end, "generate_mesh.finish")
