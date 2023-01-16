"""Creation and manipulation of system geometries."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Tuple, Type

import gmsh
import numpy as np
import pygmsh
from meshio import Mesh
from pygmsh.common.dummy import Dummy

# Type[float] indicates the object `float` rather than a float instance e.g. 1.0
Arg_Dict_Type = Dict[str, Tuple[Type[float], Type[float], Type[float]] | Type[float]]
Arg_List_Type = List[List[float] | float]
Vector = Tuple[float, float, float]


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


@dataclass
class Component:
    """Definition of a Component that should be created within a system geometry.

    Attributes:
      shape: name of the shape to use for this component
      label: unique label to apply to this component
      args: function arguments to pass to the shape constructor
    """

    shape: str
    label: str
    args: Arg_List_Type


def add_dome(
    geom: pygmsh.occ.Geometry,
    x0: Vector,
    axis: Vector,
    radius: float,
    mesh_size: float = 0.2,
) -> Dummy:
    """Add curved dome shape to a geometry.

    Args:
      geom: the geometry to modify
      x0: the centre of the circular base of the dome
      axis: the central axis of the dome
      radius: radius of the base of the dome
      mesh_size: resolution of the mesh
    """
    x0_array = np.array(x0)
    axis_array = np.array(axis)
    p0 = geom.add_point(x0, mesh_size=mesh_size)

    # generate an arbitrary unit vector perpendicular to axis
    perp_vector = np.random.rand(3)
    perp_vector -= (
        perp_vector.dot(axis_array) * axis_array / np.linalg.norm(axis_array) ** 2
    )
    perp_vector /= np.linalg.norm(perp_vector)

    xs = np.linspace(-radius, 0, 10)

    def _curve(x: float) -> float:
        """Simple quadratic function giving the shape of the curved surface."""
        return -(x**2) + 1

    curve_points = [
        geom.add_point(x0_array + perp_vector * x + _curve(x / radius) * axis_array)
        for x in xs
    ]

    lines = [
        geom.add_line(p0, curve_points[0]),
        geom.add_bspline(curve_points),
        geom.add_line(curve_points[-1], p0),
    ]
    cv = geom.add_curve_loop(lines)
    surface = geom.add_surface(cv)
    _, dome_volume, _ = geom.revolve(surface, axis_array, x0_array, -2 * np.pi)

    # remove unneeded parts of the geometry
    geom.remove(surface)
    for cp in curve_points:
        geom.remove(cp)
    for line in lines:
        geom.remove(line)
    return dome_volume


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
    args: Arg_Dict_Type


SHAPES = dict(
    box=Shape(
        name="box",
        method=pygmsh.occ.geometry.Geometry.add_box,
        args=dict(x0=(float, float, float), extents=(float, float, float)),
    ),
    ball=Shape(
        name="ball",
        method=pygmsh.occ.Geometry.add_ball,
        args=dict(x0=(float, float, float), radius=float),
    ),
    cone=Shape(
        name="cone",
        method=pygmsh.occ.Geometry.add_cone,
        args=dict(
            x0=(float, float, float),
            axis=(float, float, float),
            radius0=float,
            radius1=float,
        ),
    ),
    cylinder=Shape(
        name="cylinder",
        method=pygmsh.occ.Geometry.add_cylinder,
        args=dict(x0=(float, float, float), axis=(float, float, float), radius=float),
    ),
    dome=Shape(
        name="dome",
        method=add_dome,
        args=dict(x0=(float, float, float), axis=(float, float, float), radius=float),
    ),
)
"""Library of supported shapes."""


class ShapeFactory:
    """An adapter to pygmsh.occ.Geometry for creation of simple geometries."""

    def __init__(self, geom: pygmsh.occ.Geometry):
        """Initialise a new ShapeFactory.

        Args:
          geom: the geometry to add shapes too
          shapes:
        """
        self.geom = geom
        self.function_map = {name: shape.method for name, shape in SHAPES.items()}

    def add_component(self, component: Component, resolution: float) -> None:
        """Add a component to the system geometry.

        Args:
          component: definition of the shape to add to the system geometry
          resolution: resolution to use for mesh
        """
        shape = self.function_map[component.shape](
            self.geom, *component.args, mesh_size=resolution
        )

        # unfortunately when using the OCC geometry kernel there doesn't seem to be a
        # way to directly get the ids of the surfaces for a shape, instead we have to
        # get these directly from the gmsh module
        _, surface_tags = gmsh.model.occ.get_surface_loops(shape._id)

        self.geom.add_physical(shape, f"{component.label}_volume")
        for i, tag in enumerate(surface_tags[0]):
            self.geom.add_physical(Dummy(2, int(tag)), f"{component.label}_surface_{i}")
        return shape


def generate_mesh(components: Iterable[Component], resolution: float) -> Mesh:
    """Generate a meshio.Mesh from simple geometric components.

    Args:
      components: to include in the system geometry
      resolution: resolution to use for mesh
    """
    with Geometry() as geom:
        factory = ShapeFactory(geom)
        for component in components:
            factory.add_component(component, resolution=resolution)
        return geom.generate_mesh()
