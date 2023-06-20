"""GUI components for interacting with gmsh via a separate process."""

from dataclasses import dataclass
from multiprocessing import Process, Queue
from typing import Any, Dict, Optional, Tuple

from meshio import Mesh
from pubsub import pub
from PySide6.QtCore import QThread, Signal

from .datastore import Datastore
from .geometry import Geometry, GeometryWrapper


@dataclass
class _FunctionCall:
    """Datastructure used internally to pass information between processes."""

    name: str
    kwargs: Dict[str, Any]
    asynchronous: bool


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


class GmshDaemon:
    """Child process logic for forwarding calls to a GeometryWrapper instance.

    This class works closely with the GmshProcess class that handles the parent process
    logic for function call forwarding. Separation into separate classes minimises the
    datastructures that need to be passed to the child process and avoids serialisation
    issues on certain platforms.
    """

    def __init__(self) -> None:
        """Create a new GmshDaemon."""
        self._in_queue: Queue[_FunctionCall] = Queue()
        """Queue containing the parameters for components to be meshed."""
        self._async_out_queue: Queue[tuple[str, object] | None] = Queue()
        """Queue containing return values for asynchronous delivery."""
        self._sync_out_queue: Queue[object] = Queue()
        """Queue containing return values for synchronous delivery."""

    def run(self) -> None:
        """Main loop function that runs on the child process."""
        with Geometry() as geom:
            self.geometry_wrapper = GeometryWrapper(geom)

            while True:
                self._call_function()

    def _call_function(self) -> None:
        function_call = self._in_queue.get()

        obj = getattr(self.geometry_wrapper, function_call.name)(**function_call.kwargs)

        if function_call.asynchronous:
            self._async_out_queue.put((function_call.name, obj))
        else:
            self._sync_out_queue.put(obj)


class GmshProcess:
    """A class for communicating with gmsh on a separate process.

    Using the gmsh module seemingly only works on the main thread of the Python process,
    so in order to be able to run gmsh operations in the background, it is necessary to
    spin up a separate process for this.

    This class acts as an intermediate layer passing function calls to a GmshDaemon
    instance. Function calls may be run either synchronously or asynchronously, in which
    case the return value is injected into the GUI main loop (via a Pyside Signal on
    GmshListener) and broadcast using a pubsub message.
    """

    def __init__(self) -> None:
        """Create a new GmshProcess."""
        self.daemon = GmshDaemon()
        """"""
        self._process = Process(target=self.daemon.run, daemon=True)
        """Background process for running gmsh."""

        self._listener = GmshListener(self.daemon._async_out_queue)
        """Receives generated meshes and raises a signal when they arrive."""
        self._listener.mesh_received.connect(self._function_call_end)
        pub.subscribe(self.stop_thread, "window.close")

    def start(self) -> None:
        """Start the process and thread running."""
        self._process.start()
        self._listener.start()

    def __del__(self) -> None:
        """Stop background QThread."""
        self.stop_thread()

    def stop_thread(self) -> None:
        """Stop background QThread."""
        if self._listener.isRunning():
            # None is used as a sentinel value to signal that the thread should stop
            self.daemon._async_out_queue.put(None)
            self._listener.wait()

    def call_function(self, function_name: str, **kwargs: Any) -> object:
        """Call a GmshWrapper method and await the result.

        Args:
          function_name: name of the method to call
          kwargs: keyword arguments to pass into the method
        """
        self.daemon._in_queue.put(
            _FunctionCall(name=function_name, kwargs=kwargs, asynchronous=False)
        )
        return self.daemon._sync_out_queue.get()

    def call_function_async(self, function_name: str, **kwargs: Any) -> None:
        """Call a GmshWrapper method without awaiting the result.

        The return value will be injected into the GUI main loop via Pyside signal and
        broadcast for consumption by pubsub message.

        Args:
          function_name: name of the method to call
          kwargs: keyword arguments to pass into the method
        """
        pub.sendMessage(f"{function_name}.start")
        self.daemon._in_queue.put(
            _FunctionCall(name=function_name, kwargs=kwargs, asynchronous=True)
        )

    def _function_call_end(self, function_name: str, obj: object) -> None:
        """Event handler called when the mesh_received Signal is sent."""
        pub.sendMessage(f"{function_name}.finish", obj=obj)


gmsh_process_datastore: Datastore[str, GmshProcess] = Datastore("gmsh_process")
