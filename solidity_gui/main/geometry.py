"""Creation and manipulation of system geometries."""

from dataclasses import dataclass
from multiprocessing import Process, Queue
from threading import Thread
from typing import Callable, Dict, Iterable, List, Tuple, Type

import pygmsh
from meshio import Mesh
from pubsub import pub

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


class MeshGenerator:
    """A class for communicating with gmsh on a separate process.

    Using the gmsh module seemingly only works on the main thread of the Python process,
    so in order to be able to run gmsh operations in the background, it is necessary to
    spin up a separate process for this.
    """

    def __init__(self) -> None:
        """Create a new MeshGenerator."""
        self._in_queue: Queue = Queue()
        """Queue containing the parameters for components to be meshed."""
        self._out_queue: Queue = Queue()
        """Queue containing the generated meshes."""

        self._process = Process(target=self._run_mesh_generation, daemon=True)
        """Background process for running gmsh."""
        self._process.start()

        self._thread = Thread(target=self._run_receive_mesh, daemon=True)
        """Thread which signals when generated meshes have been received."""
        self._thread.start()

    def _generate_mesh(self) -> None:
        topic, components, resolution = self._in_queue.get()
        self._out_queue.put((topic, generate_mesh(components, resolution)))

    def _run_mesh_generation(self) -> None:
        while True:
            self._generate_mesh()

    def _receive_mesh(self) -> None:
        item: Tuple[str, Mesh] = self._out_queue.get()
        pub.sendMessage(f"{item[0]}.meshing.end", mesh=item[1])

    def _run_receive_mesh(self) -> None:
        while True:
            self._receive_mesh()

    def start_mesh_generation(
        self, topic: str, components: Iterable[Component], resolution: float
    ) -> Mesh:
        """Generate a meshio.Mesh from simple geometric components.

        Args:
            topic: the top-level topic name to send messages on
            components: to include in the system geometry
            resolution: resolution to use for mesh
        """
        pub.sendMessage(f"{topic}.meshing.begin")
        self._in_queue.put((topic, components, resolution))
