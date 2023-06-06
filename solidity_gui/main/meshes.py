"""Module for storage of mesh related data."""
import meshio
from pubsub import pub

from .datastore import Datastore
from .geometry import Component, MeshGenerator, mesh_generator_datastore

mesh_datastore: Datastore[str, meshio.Mesh] = Datastore("meshes")


current_mesh = "default"


def _add_component_to_geometry_begin(component: Component) -> None:
    """Add a new geometric component and render and display its rough mesh."""
    try:
        mesh_generator = mesh_generator_datastore[current_mesh]
    except KeyError:
        mesh_generator = MeshGenerator()
        mesh_generator_datastore[current_mesh] = mesh_generator

    mesh_generator.add_component(component)


def _add_component_to_geometry_end(mesh: meshio.Mesh) -> None:
    """Store and broadcast the resulting mesh after component addition."""
    mesh_datastore[current_mesh] = mesh
    pub.sendMessage("geometry.updated", mesh=mesh)


def _create_mesh_from_geometry_begin(size: float) -> None:
    """Generate and display a high quality mesh from the current geometry."""
    mesh_generator = mesh_generator_datastore[current_mesh]
    mesh_generator.start_mesh_generation("mesh", resolution=size)


def _create_mesh_from_geometry_end(mesh: meshio.Mesh) -> None:
    """Store and broadcast the resulting mesh after high quality mesh generation."""
    mesh_datastore[current_mesh] = mesh
    pub.sendMessage("mesh.updated", mesh=mesh)


pub.subscribe(_add_component_to_geometry_begin, "geometry.update")
pub.subscribe(_add_component_to_geometry_end, "geometry.meshing.end")
pub.subscribe(_create_mesh_from_geometry_begin, "mesh.create")
pub.subscribe(_create_mesh_from_geometry_end, "mesh.meshing.end")
