"""A module for interfacing with the Solidity command-line utility.

It achieves this by using the docker image.
"""

import contextlib
import logging
import sys
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from threading import Thread, current_thread
from typing import cast

from pubsub import pub
from python_on_whales import Container, Image, docker
from python_on_whales.exceptions import DockerException, NoSuchContainer, NoSuchImage

import solidity_gui

from ..config import (
    DOCKER_IMAGE_DIGEST,
    DOCKER_IMAGE_ID_SHORT,
    SOLIDITY_CONTAINER_NAME,
    SOLIDITY_DOCKER_IMAGE,
)
from .pubsub_decorators import pubsub_broadcast

OutputStream = Iterable[tuple[str, bytes]]


def _get_exe_folder() -> Path:
    """Get the folder of the currently executing program."""
    # Check whether we're in a Pyinstaller-bundled executable
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys.executable).parent.absolute()

    # Use the parent path of the solidity_gui module
    return Path(solidity_gui.__path__[0]).parent.absolute()


def _try_load_image() -> Image | None:
    """Try to load the image from the local filesystem."""
    exe_folder = _get_exe_folder()
    image_path = exe_folder / f"solidity_image_{DOCKER_IMAGE_ID_SHORT}.tar.gz"
    if not image_path.exists():
        return None

    # We asume that the image is the right one, as that it has the ID in the filename
    logging.info(f"Loading docker image from {image_path}...")
    tags = docker.load(str(image_path))
    image_id = ""
    for tag in tags:
        if tag.startswith("sha256:"):
            image_id = tag
            break
    if not image_id:
        logging.error(f"Image file {image_path} does not contain a valid image ID")
        return None
    img = docker.image.inspect(image_id)

    # Tag the image using the configured image digest for easier identification
    # ignoring the actual ID as this might differ between OS
    img.tag("solidity:" + DOCKER_IMAGE_DIGEST)
    return img


def _pull_image_sync() -> Image:
    """Pull the Docker image or load from local archive, if available."""
    # Check if the image is already available in Docker
    with contextlib.suppress(NoSuchImage):
        return docker.image.inspect("solidity:" + DOCKER_IMAGE_DIGEST)

    # Try to import from local filesystem
    if image := _try_load_image():
        return image

    # Fall back on doing a docker pull
    logging.info("Downloading Docker image")
    image = cast(Image, docker.pull(SOLIDITY_DOCKER_IMAGE))
    image.tag("solidity:" + DOCKER_IMAGE_DIGEST)
    return image


def _pull_image_async() -> None:
    """Pull the Docker image in the background and send a message when done."""
    Thread(
        target=pubsub_broadcast("docker.error", "docker.pulled")(_pull_image_sync)
    ).start()


def _run_solidity(
    y3d_file_path: Path,
    layout_file_path: Path,
    pellet_file_path: Path,
    materials_file_path: Path,
    num_cpus: int,
    container_name: str,
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
    try:
        container = docker.container.inspect(container_name)
        container.remove(force=True)
    except NoSuchContainer:
        pass

    # Reset flag
    _quitting = False

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

    logging.info(f"Running Docker image: {DOCKER_IMAGE_ID_SHORT}")

    # Get the Docker image
    image = _pull_image_sync()

    path_on_container = PurePosixPath("/home/software/solidity/run")
    return docker.run(
        image,
        [
            "DEMPlus",
            str(path_on_container / y3d_file_path.name),
            str(path_on_container / layout_file_path.name),
            str(path_on_container / pellet_file_path.name),
            str(path_on_container / materials_file_path.name),
        ],
        volumes=[(input_files_path.absolute(), str(path_on_container))],
        detach=not stream,
        name=container_name,
        stream=stream,
        envs={"OMP_NUM_THREADS": str(num_cpus)},
        cpus=num_cpus,
    )


def run_solidity_no_stream(
    y3d_file_path: Path,
    layout_file_path: Path,
    pellet_file_path: Path,
    materials_file_path: Path,
    num_cpus: int,
    container_name: str = SOLIDITY_CONTAINER_NAME,
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
        num_cpus: Number of CPUs to use for the Solidity process

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
            num_cpus=num_cpus,
            container_name=container_name,
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
    num_cpus: int,
    container_name: str = SOLIDITY_CONTAINER_NAME,
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
            num_cpus,
            container_name=container_name,
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
    num_cpus: int,
    container_name: str = SOLIDITY_CONTAINER_NAME,
) -> None:
    """Start Solidity in the background.

    Args:
        y3d_file_path: Path to Y3D file (BST.Y3D)
        layout_file_path: Path to file with format for elements and particles
                          (layout.txt)
        pellet_file_path: Path to file with elements and particles (pellet.txt)
        materials_file_path: Path to materials file (mat.txt)
        num_cpus: Number of CPUs to use for the Solidity process
        container_name: Name to give the Docker container
    """
    Thread(
        target=run_solidity_stream_sync,
        args=(
            y3d_file_path,
            layout_file_path,
            pellet_file_path,
            materials_file_path,
            num_cpus,
            container_name,
        ),
    ).start()


def remove_container_sync() -> int:
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
            remove_container_sync
        )
    ).start()


def _quiet_quit() -> None:
    """Quit without catching errors."""
    pub.sendMessage("docker.stopped", return_code=_return_code)
    remove_container_sync()


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
