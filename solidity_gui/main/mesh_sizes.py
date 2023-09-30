"""Module containing datastructures for assigning size data to mesh cell sets."""
from dataclasses import dataclass

from meshio import Mesh
from pubsub import pub

from .datastore import IndexDatastore


@dataclass
class MeshSize:
    """Dataclass tieing together a mesh cell set and a mesh size value."""

    cell_set_name: str
    size: float


class MeshSizeDatastore(IndexDatastore[MeshSize]):
    """Datastore for mesh size data."""


mesh_size_datastore = MeshSizeDatastore("mesh_sizes")


def _sync_sizes_mesh_removed(key: int, value: Mesh) -> None:
    """Message handler sync assignment datastore when mesh datastore changes."""
    for mesh_size_key, mesh_size in list(mesh_size_datastore.items()):
        for cell_set_name in value.cell_sets:
            if mesh_size.cell_set_name == cell_set_name:
                del mesh_size_datastore[mesh_size_key]


pub.subscribe(_sync_sizes_mesh_removed, "meshes.updated")
