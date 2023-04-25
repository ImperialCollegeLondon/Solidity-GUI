"""Module for storage of mesh related data."""
import meshio

from .datastore import IndexDatastore

mesh_datastore: IndexDatastore[meshio.Mesh] = IndexDatastore("meshes")
