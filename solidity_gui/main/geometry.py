"""Creation and manipulation of system geometries."""

from dataclasses import dataclass
from multiprocessing import Process, Queue
from typing import Callable, Dict, Iterable, List, Optional, Tuple, Type

import pygmsh
from meshio import Mesh
from pubsub import pub
from PySide6.QtCore import QThread, Signal

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


class GmshListener(QThread):
    """A class to listen for generated meshes produced in the separate gmsh process.

    We use a separate thread so that the main thread isn't blocked waiting for meshes to
    be received. Qt's signal/slot mechanism is used to pass this mesh back to the main
    thread, which invokes PyPubsub's sendMessage() function. This needs to be run on the
    main thread in case listeners want to modify the GUI (all GUI operations have to be
    on the main thread).
    """

    mesh_received = Signal(str, Mesh)
    """Signal for when a new mesh has been generated."""

    def __init__(self, queue: Queue) -> None:
        """Create a new GmshListener."""
        super().__init__()
        self._queue = queue

    def _receive_mesh(self) -> bool:
        """Read a new mesh from the queue.

        Returns:
            False if thread is being stopped, True if item was retrieved successfully
        """
        item: Optional[Tuple[str, Mesh]] = self._queue.get()
        if not item:
            return False

        self.mesh_received.emit(*item)
        return True

    def run(self) -> None:
        """Read received meshes forever and broadcast via a signal."""
        while self._receive_mesh():
            pass


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

        self._listener = GmshListener(self._out_queue)
        """Receives generated meshes and raises a signal when they arrive."""
        self._listener.mesh_received.connect(self._send_meshing_end)
        self._listener.start()

    def __del__(self) -> None:
        """Stop background QThread."""
        # None is used as a sentinel value to signal that the thread should stop
        self._out_queue.put(None)
        self._listener.wait()

    def _generate_mesh(self) -> None:
        topic, components, resolution = self._in_queue.get()
        self._out_queue.put((topic, generate_mesh(components, resolution)))

    def _run_mesh_generation(self) -> None:
        while True:
            self._generate_mesh()

    def _send_meshing_end(self, name: str, mesh: Mesh) -> None:
        pub.sendMessage(f"{name}.meshing.end", mesh=mesh)

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
