"""Creation and manipulation of system geometries."""

import warnings
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from itertools import chain
from typing import Any

import gmsh
import numpy as np
import pygmsh
from marshmallow import ValidationError, validate
from meshio import Mesh
from pygmsh.common.dummy import Dummy

from .forms import Form
from .forms.fields import FloatField, VectorField

Vector = tuple[float, float, float]


class Surface(pygmsh.common.surface.Surface):
    """Generates a Surface from CurveLoop.

    This class includes a necessary bug fix when working with the OCC geometry kernel.
    Raised with pygmsh project - https://github.com/meshpro/pygmsh/issues/567. If this
    issue is resolved this class can be removed.
    """

    def __init__(
        self,
        env: gmsh.model.geo | gmsh.model.occ,
        curve_loop: pygmsh.common.curve_loop.CurveLoop,
    ):
        """Create a new Surface instance.

        Args:
          env: gmsh interface to either the built-in or OCC geometry kernel
          curve_loop: contains all the Line objects for the loop construction
        """
        assert isinstance(curve_loop, pygmsh.common.curve_loop.CurveLoop)
        self.curve_loop = curve_loop
        self.num_edges = len(curve_loop)
        self._id = env.addSurfaceFilling(self.curve_loop._id)  # fixed line
        self.dim_tag = (2, self._id)
        self.dim_tags = [self.dim_tag]


class Geometry(pygmsh.occ.Geometry):
    """Interface to gmsh geometry functionality.

    This version of the Geometry interface updates the `add_surface` method to use a
    custom Surface class in order circumvent issue #567 of meshpro/pymsh.
    """

    def add_surface(self, *args: Any, **kwargs: Any) -> Surface:
        """Add a new surface to the geometry."""
        return Surface(self.env, *args, **kwargs)

    def boolean_union(
        self,
        entities: list[Dummy],
        delete_first: bool = True,
        delete_other: bool = True,
    ) -> list[Dummy]:
        """Perform a boolean union of geometric entities.

        A thin wrapper around pygmsh.occ.Geometry that suppresses warnings.
        """
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message=".*Specified mesh size.*", module=".*geometry"
            )
            return super().boolean_union(entities, delete_first, delete_other)

    def boolean_fragments(
        self,
        d0: Dummy,
        d1: Dummy,
        delete_first: bool = True,
        delete_other: bool = True,
    ) -> list[Dummy]:
        """Perform a boolean union of geometric entities.

        A thin wrapper around pygmsh.occ.Geometry that suppresses warnings.
        """
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message=".*Specified mesh size.*", module=".*geometry"
            )
            return super().boolean_fragments(d0, d1, delete_first, delete_other)


@dataclass
class Component:
    """Definition of a Component that should be created within a system geometry.

    Attributes:
      shape: name of the shape to use for this component
      label: unique label to apply to this component
      kwargs: function arguments to pass to the shape constructor
    """

    shape: str
    label: str
    kwargs: dict[str, float | list[float]]


@dataclass
class Shape:
    """Definition of a shape.

    Contains the information required by ShapeFactory to build a shape using the
    pygmsh.occ.Geometry class.

    Attributes:
      name: name of the shape e.g. "box"
      method: method that is called to create a shape instance
      args: mapping of method arguments to expected types
    """

    name: str
    method: Callable
    form: type[Form]


greater_than_zero = validate.Range(min=0, min_inclusive=False)


class BoxForm(Form):
    """Form defining data required for box shape creation."""

    x0 = VectorField(display_name="Corner Coordinates")
    extents = VectorField(
        display_name="Side Lengths",
        description="Length of box sides in x, y and z dimensions.",
        validators=[validate.NoneOf([0.0])],
    )


class BallForm(Form):
    """Form defining data required for ball shape creation."""

    center = VectorField(display_name="Center Coordinates")
    radius = FloatField(
        description="The radius of the ball.",
        validators=[greater_than_zero],
    )


def non_zero_magnitude(vector: list[float], **kwargs: Any) -> None:
    """Validate vector data has a magnitude greater than zero.

    Args:
      vector: vector data
      **kwargs: additional keyword arguments passed to Marshmallow validators
    """
    if np.linalg.norm(vector) == 0.0:
        raise ValidationError("Vector must have non-zero magnitude.")


class ConeForm(Form):
    """Form defining data required for cone shape creation."""

    center = VectorField(display_name="Base Center Coordinates")
    axis = VectorField(
        display_name="Axis Vector", vector_validators=[non_zero_magnitude]
    )
    radius0 = FloatField(
        display_name="Base Radius",
        validators=[greater_than_zero],
    )
    radius1 = FloatField(
        display_name="Tip Radius",
        validators=[validate.Range(min=0, min_inclusive=True)],
    )

    def validate(self, data: dict[str, Any], **kwargs: Any) -> None:
        """Schema level validator."""
        if data["radius1"] >= data["radius0"]:
            raise ValidationError("Base radius must be larger than tip radius.")


class CylinderForm(Form):
    """Form defining data required for cylinder shape creation."""

    x0 = VectorField(display_name="Base Center Coordinates")
    axis = VectorField(
        display_name="Axis Vector", vector_validators=[non_zero_magnitude]
    )
    radius = FloatField(validators=[greater_than_zero])


SHAPES = dict(
    box=Shape(name="box", method=pygmsh.occ.geometry.Geometry.add_box, form=BoxForm),
    ball=Shape(name="ball", method=pygmsh.occ.Geometry.add_ball, form=BallForm),
    cone=Shape(name="cone", method=pygmsh.occ.Geometry.add_cone, form=ConeForm),
    cylinder=Shape(
        name="cylinder", method=pygmsh.occ.Geometry.add_cylinder, form=CylinderForm
    ),
)
"""Library of supported shapes."""


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


def get_shared_surfaces(volumes: list[Dummy]) -> set[tuple[Dummy, Dummy]]:
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

    shared_surfaces = set()
    for tag in repeated_surface_tags:
        volume_tags = [i for i, surface in enumerate(surface_tags) if tag in surface]
        if len(volume_tags) != 2:
            raise ValueError("Error detecting shared surfaces in geometry.")
        shared_surfaces.add((volumes[volume_tags[0]], volumes[volume_tags[1]]))
    return shared_surfaces
