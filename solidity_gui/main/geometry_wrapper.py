"""Module for GeometryWrapper class."""

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import chain

import gmsh
import numpy as np
import pygmsh
from meshio import Mesh
from meshio.gmsh import gmsh_to_meshio_type
from pygmsh.common.dummy import Dummy

from .components import Component
from .geometry import DIM_2_CELL_TYPE, SHAPES
from .mesh_sizes import MeshSize


@dataclass
class Entity:
    """Representation of a geometric entity."""

    name: str
    dim: int
    tag: int

    @property
    def dim_tag(self) -> tuple[int, int]:
        """Return dimension and tag values as tuple compatible with gmsh functions."""
        return (self.dim, self.tag)


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
        self.entities: list[Entity] = []

    def add_component(
        self, component: Component, mesh_size: float | None = None
    ) -> Mesh:
        """Add a component to the system geometry.

        Args:
          component: definition of the shape to add to the system geometry
          mesh_size: size applied to mesh (if None mesh size is determined by gmsh)
        """
        shapes = self.function_map[component.shape](self.geom, **component.kwargs)
        # below fudge allows some functions to return more than one shape
        # we could avoid this by making all shape functions return a list but that would
        # involve wrapping all of the pygmsh functions
        if not isinstance(shapes, list):
            shapes = [shapes]
        self.geom.synchronize()
        return self._generate_mesh(default_size=mesh_size)

    def _generate_mesh(
        self,
        mesh_sizes: Iterable[MeshSize] = [],
        default_size: float | None = None,
        imported=False,
    ) -> Mesh:
        if imported:
            mesh = self.geom.generate_mesh()
            create_surfaces()
        else:
            # we have to manually clear the old mesh before we can generate a new one
            gmsh.model.mesh.clear()
            gmsh.model.mesh.remove_constraints()

            points_with_sizes = set()
            for entity_name in ("volume", "surface", "line", "point"):
                for mesh_size in mesh_sizes:
                    if entity_name not in mesh_size.cell_set_name:
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
                        set(gmsh.model.get_entities(dim=0)).difference(
                            points_with_sizes
                        )
                    ),
                    default_size,
                )
            mesh = self.geom.generate_mesh()

        # create a cell set for each geometric entity
        cell_sets = {}
        cell_set_to_entity = {}
        entities = []
        counter: Counter[int] = Counter()
        for dim, tag in gmsh.model.getEntities():
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
            entity = Entity(name, dim, tag)
            entities.append(entity)
            cell_set_to_entity[name] = entity.dim_tag
        mesh.cell_sets = cell_sets
        self.entities = entities
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
        return self._generate_mesh(imported=True)

    def merge_mesh(self, filename: str) -> None:
        """Merge a mesh into the current geometry."""
        gmsh.merge(filename)

    def write_file(self, filename: str) -> None:
        """Export the current geometry/mesh to a file."""
        gmsh.write(filename)

    def get_joined_volumes(self) -> set[tuple[str, str]]:
        """Get the cell_set_names of volumes that share a surface."""
        volumes = [Dummy(*dim_tags) for dim_tags in gmsh.model.get_entities(dim=3)]
        joined_volumes = get_joined_volumes(volumes)
        return {
            (
                self._get_entity_by_shape(vol1).name,
                self._get_entity_by_shape(vol2).name,
            )
            for vol1, vol2 in joined_volumes
        }

    def _get_entity_by_shape(self, shape: Dummy) -> Entity:
        for entity in self.entities:
            if entity.dim_tag == shape.dim_tag:
                return entity
        raise ValueError(f"Unable to find entity for shape: {shape}")


def get_joined_volumes(volumes: list[Dummy]) -> list[tuple[Dummy, Dummy]]:
    """Detect the shared surfaces between a set of volumes in the active gmsh model.

    Args:
      volumes: the volumes to check
    """
    surface_tags = [
        list(gmsh.model.occ.get_surface_loops(vol._id)[1][0]) for vol in volumes
    ]
    repeated_surface_tags = [
        item for item, count in Counter(chain(*surface_tags)).items() if count > 1
    ]

    shared_surfaces = []
    for tag in repeated_surface_tags:
        volume_tags = [i for i, surface in enumerate(surface_tags) if tag in surface]
        if len(volume_tags) != 2:
            raise ValueError("Error detecting shared surfaces in geometry.")
        joined_volumes = (volumes[volume_tags[0]], volumes[volume_tags[1]])
        if (
            joined_volumes not in shared_surfaces
            and joined_volumes[::-1] not in shared_surfaces
        ):
            shared_surfaces.append(joined_volumes)
    return shared_surfaces


def compute_normal(triangle, nodes, node_tags):
    # Extract the coordinates of the triangle vertices
    p1 = np.array(nodes[np.argmax(node_tags == triangle[0])])
    p2 = np.array(nodes[np.argmax(node_tags == triangle[1])])
    p3 = np.array(nodes[np.argmax(node_tags == triangle[2])])

    # Compute vectors
    v1 = p2 - p1
    v2 = p3 - p1

    # Compute the normal vector using the cross product
    normal = np.cross(v1, v2)

    # Normalize the normal vector
    normal = normal / np.linalg.norm(normal)

    return normal


def angle_between_normals(normal1, normal2):
    # Compute the dot product of the normals
    dot_product = np.dot(normal1, normal2)

    # Compute the angle in radians and convert to degrees
    angle = np.arccos(dot_product) * 180 / np.pi

    return angle


def flag_sharp_angles(triangle_tags, triangles, node_tags, nodes, threshold=30):
    normals = [compute_normal(triangle, nodes, node_tags) for triangle in triangles]
    surfaces = []
    neighbours_found = defaultdict(int)

    for i in range(len(triangles)):
        for j in range(i + 1, len(triangles)):
            # We compare only first neighbours, which share two nodes
            if not len(set(triangles[i]).intersection(triangles[j])) == 2:
                continue

            neighbours_found[i] += 1
            neighbours_found[j] += 1
            angle = angle_between_normals(normals[i], normals[j])
            if not threshold < angle < 180 - threshold:
                surfaces.append([triangle_tags[i], triangle_tags[j]])

            # surfaces.append((triangle_tags[i], triangle_tags[j]))
            # If we have 3 neighbours, we break the loop and move to the next triangle
            if neighbours_found[i] == 3:
                break

    return sorted(surfaces)


def cluster_into_surfaces(pairs):
    """Cluster pairs of triangles into surfaces."""
    out = []
    while len(pairs) > 0:
        first, *rest = pairs
        first = set(first)

        lf = -1
        while len(first) > lf:
            lf = len(first)

            rest2 = []
            for r in rest:
                if len(first.intersection(set(r))) > 0:
                    first |= set(r)
                else:
                    rest2.append(r)
            rest = rest2

        out.append(first)
        pairs = rest
    return out


def create_surfaces(threshold: int = 30):
    """Create surfaces based on the angle of first neighbours."""
    node_tags, nodes_coord, _ = gmsh.model.mesh.getNodes()
    nodes_coord = nodes_coord.reshape(-1, 3)

    # Get triangle coordinates
    _, [tri_tags], [tri_coord] = gmsh.model.mesh.getElements(2)
    tri_coord = tri_coord.reshape(-1, 3)

    # Dict of the triangle ids and their node coordinates
    tri_id_to_coords = {tag: coord for tag, coord in zip(tri_tags, tri_coord)}

    flagged_pairs = flag_sharp_angles(
        tri_tags, tri_coord, node_tags, nodes_coord, threshold
    )
    surfaces = cluster_into_surfaces(flagged_pairs)

    for tag in range(len(surfaces)):
        gmsh.model.addDiscreteEntity(2, tag + 1)

    element_type = 2  # Triangle
    for i, surface_tri in enumerate(surfaces):
        flat_node_tags = list([i for tri in surface_tri for i in tri_id_to_coords[tri]])
        gmsh.model.mesh.addElementsByType(
            i + 1, element_type, list(surface_tri), flat_node_tags
        )

    if (2, 0) in gmsh.model.getEntities():
        gmsh.model.removeEntities(
            [
                (2, 0),
            ]
        )
