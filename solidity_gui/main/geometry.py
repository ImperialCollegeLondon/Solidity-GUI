"""Creation and manipulation of system geometries."""

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Tuple, Type

import pygmsh
from meshio import Mesh

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
    pygmsh.geo.Geometry class.

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
        method=pygmsh.geo.Geometry.add_box,
        args=dict(x0=float, x1=float, y0=float, y1=float, z0=float, z1=float),
    ),
    ball=Shape(
        name="ball",
        method=pygmsh.geo.Geometry.add_ball,
        args=dict(x0=(float, float, float), radius=float),
    ),
)
"""Library of supported shapes."""


class ShapeFactory:
    """An adapter to pygmsh.geo.Geometry for creation of simple geometries."""

    def __init__(self, geom: pygmsh.geo.Geometry):
        """Initialise a new ShapeFactory.

        Args:
          geom: the geometry to add shapes too
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
        self.geom.add_physical(shape.volume, f"{component.label}_volume")
        for i, surface in enumerate(shape.surface_loop.surfaces):
            self.geom.add_physical(surface, f"{component.label}_surface_{i}")


def generate_mesh(components: Iterable[Component], resolution: float) -> Mesh:
    """Generate a meshio.Mesh from simple geometric components.

    Args:
      components: to include in the system geometry
      resolution: resolution to use for mesh
    """
    with pygmsh.geo.Geometry() as geom:
        factory = ShapeFactory(geom)
        for component in components:
            factory.add_component(component, resolution=resolution)
        return geom.generate_mesh()
