"""Module for GeometryWrapper class."""
from collections import Counter
from collections.abc import Iterable

import gmsh
import numpy as np
import pygmsh
from meshio import Mesh
from meshio.gmsh import gmsh_to_meshio_type

from .components import Component
from .geometry import DIM_2_CELL_TYPE, SHAPES
from .mesh_sizes import MeshSize


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
        self.cell_set_to_entity: dict[str, tuple[int, int]] = dict()

    def add_component(
        self, component: Component, mesh_size: float | None = None
    ) -> Mesh:
        """Add a component to the system geometry.

        Args:
          component: definition of the shape to add to the system geometry
          mesh_size: size applied to mesh if None mesh size is determined by gmsh
        """
        shapes = self.function_map[component.shape](
            self.geom, **component.kwargs  # , mesh_size=resolution
        )
        # below fudge allows some functions to return more than one shape
        # we could avoid this by making all shape functions return a list but that would
        # involve wrapping all of the pygmsh functions
        if not isinstance(shapes, list):
            shapes = [shapes]
        self.geom.synchronize()
        return self._generate_mesh(default_size=mesh_size)

    def _generate_mesh(
        self, mesh_sizes: Iterable[MeshSize] = [], default_size: float | None = None
    ) -> Mesh:
        # we have to manually clear the old mesh before we can generate a new one
        gmsh.model.mesh.clear()
        gmsh.model.mesh.remove_constraints()

        points_with_sizes = set()
        for entity in ("volume", "surface", "line", "point"):
            for mesh_size in mesh_sizes:
                if entity not in mesh_size.cell_set_name:
                    continue
                try:
                    dim_tag = self.cell_set_to_entity[mesh_size.cell_set_name]
                except KeyError:
                    continue
                points = gmsh.model.get_boundary((dim_tag,), False, False, True)
                gmsh.model.mesh.set_size(points, mesh_size.size)
                points_with_sizes.update(points)

        if default_size is not None:
            gmsh.model.mesh.set_size(
                tuple(
                    set(gmsh.model.get_entities(dim=0)).difference(points_with_sizes)
                ),
                default_size,
            )
        mesh = self.geom.generate_mesh()

        # create a cell set for each geometric entity
        cell_sets = {}
        cell_set_to_entity = {}
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
            cell_set_to_entity[name] = (dim, tag)
        mesh.cell_sets = cell_sets
        self.cell_set_to_entity = cell_set_to_entity
        return mesh

    def generate_mesh(
        self, mesh_sizes: Iterable[MeshSize], default_size: float
    ) -> Mesh:
        """Generate a new system mesh at the specified resolution.

        Args:
            mesh_sizes: assignment of mesh size values to cell sets
            default_size: mesh size applied to points without a mesh size assignment
        """
        return self._generate_mesh(mesh_sizes, default_size)

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
