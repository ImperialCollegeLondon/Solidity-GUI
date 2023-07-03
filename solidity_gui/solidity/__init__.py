"""A module for interfacing with the Solidity command-line utility.

It achieves this by using the docker image.
"""
import atexit
import logging
from pathlib import Path, PurePosixPath
from typing import Iterable, cast

from pubsub import pub
from python_on_whales import Container, docker
from python_on_whales.exceptions import NoSuchContainer

from ..config import SOLIDITY_CONTAINER_NAME, SOLIDITY_DOCKER_IMAGE

OutputStream = Iterable[tuple[str, bytes]]


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
    # Remove the Solidity container if it already exists
    _remove_container()

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


def run_solidity_stream(
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
    # Start Solidity. TODO: Error handling
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

    # Signal that the container has been started
    pub.sendMessage("docker.started", output_stream=output_stream)


def _remove_container() -> None:
    """Remove the Solidity container.

    If the container does not exist, nothing will happen.
    """
    try:
        container = docker.container.inspect(SOLIDITY_CONTAINER_NAME)
    except NoSuchContainer:
        return

    logging.info(f"Stopping Docker container ({container})...")

    try:
        container.stop()
    except Exception:
        pass
    try:
        container.remove()
    except Exception:
        pass

    pub.sendMessage("docker.stopped")


# Listen for Docker-related messages
pub.subscribe(run_solidity_stream, "docker.start")
pub.subscribe(_remove_container, "docker.stop")


# Make sure container is always removed on program exit
atexit.register(_remove_container)
