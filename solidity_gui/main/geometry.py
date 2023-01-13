"""Creation and manipulation of system geometries."""

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Tuple, Type

import gmsh
import pygmsh
from meshio import Mesh
from pygmsh.common.dummy import Dummy

# Type[float] indicates the object `float` rather than a float instance e.g. 1.0
Arg_Dict_Type = Dict[str, Tuple[Type[float], Type[float], Type[float]] | Type[float]]
Arg_List_Type = List[List[float] | float]


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
    with pygmsh.occ.geometry.Geometry() as geom:
        factory = ShapeFactory(geom)
        for component in components:
            factory.add_component(component, resolution=resolution)
        return geom.generate_mesh()
