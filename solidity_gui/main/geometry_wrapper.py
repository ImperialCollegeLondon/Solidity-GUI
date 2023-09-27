"""Module for GeometryWrapper class."""
from collections import Counter

import gmsh
import numpy as np
import pygmsh
from meshio import Mesh
from meshio.gmsh import gmsh_to_meshio_type

from .components import Component
from .geometry import DIM_2_CELL_TYPE, SHAPES


class GeometryWrapper:
    """An adapter to pygmsh.occ.Geometry for creation of simple geometries."""

    def __init__(self, geom: pygmsh.occ.Geometry, label: str):
        """Initialise a new ShapeFactory.

        Args:
          geom: the geometry to add shapes too
          label: text label identiying the geometry
        """
        self.geom = geom
        self.function_map = {name: shape.method for name, shape in SHAPES.items()}
        self.label = label

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

        return self._generate_mesh()

    def _generate_mesh(self) -> Mesh:
        # we have to manually clear the old mesh before we can generate a new one
        gmsh.model.mesh.clear()
        mesh = self.geom.generate_mesh()

        # create a cell set for each geometric entity
        cell_sets = {}
        counter: Counter[int] = Counter()
        for dim, tag in gmsh.model.occ.get_entities():
            cell_type = DIM_2_CELL_TYPE[dim]
            try:
                [element_type], [element_indexes], _ = gmsh.model.mesh.getElements(
                    dim, tag
                )
            except ValueError:
                continue
            cell_set_id = counter[dim]
            name = f"{self.label}_{cell_type}_{cell_set_id}"
            counter[dim] += 1
            cell_sets[name] = [
                (
                    element_indexes - 1
                    if cell_block.type == gmsh_to_meshio_type[element_type]
                    else None
                )
                for cell_block in mesh.cells
            ]
        mesh.cell_sets = cell_sets
        return mesh

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
        return self._generate_mesh()
