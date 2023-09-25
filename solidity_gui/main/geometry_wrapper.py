"""Module for GeometryWrapper class."""

import gmsh
import numpy as np
import pygmsh
from meshio import Mesh
from pygmsh.common.dummy import Dummy

from .components import Component
from .geometry import SHAPES


class GeometryWrapper:
    """An adapter to pygmsh.occ.Geometry for creation of simple geometries."""

    def __init__(self, geom: pygmsh.occ.Geometry):
        """Initialise a new ShapeFactory.

        Args:
          geom: the geometry to add shapes too
        """
        self.geom = geom
        self.function_map = {name: shape.method for name, shape in SHAPES.items()}

    def add_component(self, component: Component, resolution: float) -> Mesh:
        """Add a component to the system geometry.

        Args:
          component: definition of the shape to add to the system geometry
          resolution: resolution to use for mesh
        """
        shapes = self.function_map[component.shape](
            self.geom, **component.kwargs, mesh_size=resolution
        )
        # below fudge allows some functions to return more than one shape
        # we could avoid this by making all shape functions return a list but that would
        # involve wrapping all of the pygmsh functions
        if not isinstance(shapes, list):
            shapes = [shapes]

        # unfortunately when using the OCC geometry kernel there doesn't seem to be a
        # way to directly get the ids of the surfaces for a shape, instead we have to
        # get these directly from the gmsh module
        surface_count = 0
        for shape_count, shape in enumerate(shapes):
            _, surface_tags = gmsh.model.occ.get_surface_loops(shape._id)
            self.geom.add_physical(shape, f"{component.label}_volume_{shape_count}")
            for tag in surface_tags[0]:
                self.geom.add_physical(
                    Dummy(2, int(tag)), f"{component.label}_surface_{surface_count}"
                )
                surface_count += 1
        return self._generate_mesh()

    def _generate_mesh(self) -> Mesh:
        # we have to manually clear out some of the mesh and physical group info
        # before we can generate a new mesh
        gmsh.model.mesh.clear()
        for dim_tag in gmsh.model.get_physical_groups():
            gmsh.model.remove_physical_name(gmsh.model.get_physical_name(*dim_tag))
        gmsh.model.remove_physical_groups()
        return self.geom.generate_mesh()

    def generate_mesh(self, resolution: float) -> Mesh:
        """Generate a new system mesh at the specified resolution.

        Args:
            resolution: desired mesh resolution
        """
        self.geom._SIZE_QUEUE = [(sq[0], resolution) for sq in self.geom._SIZE_QUEUE]
        return self._generate_mesh()

    def get_surface_nodes(self) -> np.ndarray:
        """Get the indices of the mesh nodes that are on the system surface."""
        volume_dim_tags = gmsh.model.get_entities(dim=3)
        surface_dim_tags = gmsh.model.get_boundary(volume_dim_tags, oriented=False)
        nodes = [
            gmsh.model.mesh.getNodes(*dim_tags, includeBoundary=True)[0]
            for dim_tags in surface_dim_tags
        ]
        return np.sort(np.unique(np.concatenate(nodes))) - 1

    def import_geometry(self, geom_name: str, filename: str) -> Mesh:
        """Import a system geometry from an input file."""
        gmsh.open(filename)
        for dim, label in ((2, "surface"), (3, "volume")):
            i = 0
            for dimtag in self.geom.env.getEntities(dim=dim):
                self.geom.add_physical(Dummy(*dimtag), f"{geom_name}_{label}_{i}")
                i += 1
        return self._generate_mesh()
