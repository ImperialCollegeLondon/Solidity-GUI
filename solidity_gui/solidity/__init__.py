"""A module for interfacing with the Solidity command-line utility.

It achieves this by using the docker image.
"""
import atexit
import logging
from pathlib import Path, PurePosixPath
from threading import Thread, current_thread
from typing import Iterable, cast

from pubsub import pub
from python_on_whales import Container, docker
from python_on_whales.exceptions import DockerException, NoSuchContainer

from ..config import SOLIDITY_CONTAINER_NAME, SOLIDITY_DOCKER_IMAGE
from .pubsub_decorators import pubsub_broadcast

OutputStream = Iterable[tuple[str, bytes]]


def _pull_image_async(docker_image: str = SOLIDITY_DOCKER_IMAGE) -> None:
    """Pull the Docker image in the background and send a message when done."""
    Thread(
        target=pubsub_broadcast("docker.error", "docker.pulled")(docker.pull),
        args=(docker_image,),
    ).start()


def _run_solidity(
    y3d_file_path: Path,
    layout_file_path: Path,
    pellet_file_path: Path,
    materials_file_path: Path,
    docker_image: str,
    stream: bool,
) -> Container | str | OutputStream:
    """Run Solidity using the specified input files, using docker.run().

    All the input files must be in the same directory as one another.

    Args:
        y3d_file_path: Path to Y3D file (BST.Y3D)
        layout_file_path: Path to file with format for elements and particles
                          (layout.txt)
        pellet_file_path: Path to file with elements and particles (pellet.txt)
        materials_file_path: Path to materials file (mat.txt)
        docker_image: URL and tag/SHA of docker image
        stream: Whether to stream stdout and stderr as an iterator

    Returns:
        Return value from docker.run()

    Raises:
        ValueError: If input files are not in same directory
        RuntimeError: If any of the input files do not exist or the Docker image is
                      already running
    """
    global _quitting, _return_code

    # Assume success until we hear otherwise (i.e. a DockerException is raised)
    _return_code = 0

    # Remove the Solidity container if it already exists
    _remove_container_sync()

    # Reset flag
    _quitting = False

    logging.info("Starting Solidity")

    input_files_path = y3d_file_path.parent
    if not all(
        p.parent.samefile(input_files_path)
        for p in (layout_file_path, pellet_file_path, materials_file_path)
    ):
        raise ValueError("All input files must be in the same directory")

    # Solidity will exit if any of the input files do not exist, but let's help our
    # users out by raising an error at this stage, so they don't have to wade through
    # the logs to find this out
    for p in (y3d_file_path, layout_file_path, pellet_file_path, materials_file_path):
        if not p.is_file():
            raise RuntimeError(f"File {p} does not exist")

    logging.info(
        f"(Files: {input_files_path}/: {y3d_file_path.name}, {layout_file_path.name}, "
        f"{pellet_file_path.name}, {materials_file_path.name})"
    )

    logging.info(f"Running Docker image: {docker_image}")

    path_on_container = PurePosixPath("/home/software/solidity/run")
    return docker.run(
        docker_image,
        [
            "DEMPlus",
            str(path_on_container / y3d_file_path.name),
            str(path_on_container / layout_file_path.name),
            str(path_on_container / pellet_file_path.name),
            str(path_on_container / materials_file_path.name),
        ],
        volumes=[(input_files_path.absolute(), str(path_on_container))],
        detach=not stream,
        name=SOLIDITY_CONTAINER_NAME,
        stream=stream,
    )


def run_solidity_no_stream(
    y3d_file_path: Path,
    layout_file_path: Path,
    pellet_file_path: Path,
    materials_file_path: Path,
) -> Container:
    """Run Solidity using the specified input files.

    Stdout and stderr will be printed to the console.

    All the input files must be in the same directory as one another.

    Args:
        y3d_file_path: Path to Y3D file (BST.Y3D)
        layout_file_path: Path to file with format for elements and particles
                          (layout.txt)
        pellet_file_path: Path to file with elements and particles (pellet.txt)
        materials_file_path: Path to materials file (mat.txt)

    Returns:
        The running container

    Raises:
        ValueError: If input files are not in same directory
        RuntimeError: If any of the input files do not exist or the Docker image is
                      already running
    """
    # Start Solidity
    return cast(
        Container,
        _run_solidity(
            y3d_file_path,
            layout_file_path,
            pellet_file_path,
            materials_file_path,
            SOLIDITY_DOCKER_IMAGE,
            stream=False,
        ),
    )


class _OutputThread(Thread):
    def __init__(self, stream: OutputStream) -> None:
        super().__init__(target=self._run)
        self._stream = stream

    def _run(self) -> None:
        global _quitting

        try:
            for type, output_bytes in self._stream:
                if _quitting:
                    return

                # Remove trailing newline
                output = output_bytes[:-1].decode(errors="replace")

                # We send different messages depending on whether output is stdout or
                # stderr
                pub.sendMessage(f"docker.output.{type}", output=output)
        except DockerException as error:
            if not _quitting:
                pub.sendMessage("docker.error", error=error)
        else:
            # Otherwise the container has exited normally
            if not _quitting:
                _quiet_quit()


@pubsub_broadcast("docker.error", "docker.started")
def run_solidity_stream_sync(
    y3d_file_path: Path,
    layout_file_path: Path,
    pellet_file_path: Path,
    materials_file_path: Path,
) -> None:
    """Run Solidity using the specified input files.

    Stdout and stderr are output as an iterator broadcast on the docker.started signal.

    All the input files must be in the same directory as one another.

    Args:
        y3d_file_path: Path to Y3D file (BST.Y3D)
        layout_file_path: Path to file with format for elements and particles
                          (layout.txt)
        pellet_file_path: Path to file with elements and particles (pellet.txt)
        materials_file_path: Path to materials file (mat.txt)

    Raises:
        ValueError: If input files are not in same directory
        RuntimeError: If any of the input files do not exist or the Docker image is
                      already running
    """
    global _output_thread

    # Start Solidity
    output_stream = cast(
        OutputStream,
        _run_solidity(
            y3d_file_path,
            layout_file_path,
            pellet_file_path,
            materials_file_path,
            SOLIDITY_DOCKER_IMAGE,
            stream=True,
        ),
    )

    # Listen for stdout and stderr in background
    _output_thread = _OutputThread(output_stream)
    _output_thread.start()


def run_solidity_stream_async(
    y3d_file_path: Path,
    layout_file_path: Path,
    pellet_file_path: Path,
    materials_file_path: Path,
) -> None:
    """Start Solidity in the background.

    Args:
        y3d_file_path: Path to Y3D file (BST.Y3D)
        layout_file_path: Path to file with format for elements and particles
                          (layout.txt)
        pellet_file_path: Path to file with elements and particles (pellet.txt)
        materials_file_path: Path to materials file (mat.txt)
    """
    Thread(
        target=run_solidity_stream_sync,
        args=(y3d_file_path, layout_file_path, pellet_file_path, materials_file_path),
    ).start()


def _remove_container_sync() -> int:
    """Remove the Solidity container.

    If the container does not exist, nothing will happen.
    """
    global _output_thread, _quitting, _return_code
    try:
        container = docker.container.inspect(SOLIDITY_CONTAINER_NAME)
    except NoSuchContainer:
        return _return_code

    logging.info(f"Stopping Docker container ({container})...")
    _quitting = True

    try:
        container.stop()
    except Exception:
        pass
    try:
        container.remove()
    except Exception:
        pass

    if _output_thread:
        # Threads can't join themselves
        if _output_thread.ident != current_thread().ident:
            _output_thread.join()

        _output_thread = None

    return _return_code


def _remove_container_async() -> None:
    """Remove the Solidity container on a background thread and signal when done."""
    Thread(
        target=pubsub_broadcast("docker.error", "docker.stopped", "return_code")(
            _remove_container_sync
        )
    ).start()


def _quiet_quit() -> None:
    """Quit without catching errors."""
    pub.sendMessage("docker.stopped", return_code=_return_code)
    _remove_container_sync()


def _on_docker_error(error: BaseException) -> None:
    global _return_code
    if isinstance(error, DockerException):
        _return_code = error.return_code

    # For now, assume all errors are fatal
    _quiet_quit()


_return_code: int = 0
"""Return code from the Docker process."""

_quitting: bool = False
"""Whether the Docker container is exiting."""

_output_thread: _OutputThread | None = None
"""Thread to read container's stdout and stderr in background."""


# Listen for Docker-related messages
pub.subscribe(_pull_image_async, "docker.pull")
pub.subscribe(run_solidity_stream_async, "docker.start")
pub.subscribe(_remove_container_async, "docker.stop")

# Stop container if an error occurs
pub.subscribe(_on_docker_error, "docker.error")

# Make sure container is always removed on program exit
atexit.register(_remove_container_sync)
