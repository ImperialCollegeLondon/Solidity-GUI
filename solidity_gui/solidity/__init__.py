"""A module for interfacing with the Solidity command-line utility.

It achieves this by using the docker image.
"""
import logging
import sys
from pathlib import Path, PurePosixPath
from typing import Iterable, cast

from python_on_whales import Container, Image, docker
from python_on_whales.exceptions import NoSuchImage

import solidity_gui

from ..config import (
    DOCKER_IMAGE_ID,
    DOCKER_IMAGE_ID_SHORT,
    SOLIDITY_CONTAINER_NAME,
    SOLIDITY_DOCKER_IMAGE,
)

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

    logging.info(f"Loading docker image from {image_path}...")
    docker.load(str(image_path))

    try:
        return docker.image.inspect(DOCKER_IMAGE_ID)
    except NoSuchImage:
        # This is an eminently unlikely outcome given that we embed the image ID in the
        # filename, but let's be extra careful
        logging.warn("Image ID for local file is wrong; ignoring")
        return None


def pull_image() -> Image:
    """Pull the Docker image or load from local archive, if available."""
    # Check if the image is already available in Docker
    try:
        return docker.image.inspect(DOCKER_IMAGE_ID)
    except NoSuchImage:
        pass

    # Try to import from local filesystem
    if image := _try_load_image():
        return image

    # Fall back on doing a docker pull
    logging.info("Downloading Docker image")
    return cast(Image, docker.pull(SOLIDITY_DOCKER_IMAGE))


def _run_solidity(
    y3d_file_path: Path,
    layout_file_path: Path,
    pellet_file_path: Path,
    materials_file_path: Path,
    detach: bool,
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
    image = pull_image()

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
        detach=detach,
        name=SOLIDITY_CONTAINER_NAME,
    )


def remove_container(container: Container) -> None:
    """Remove the Solidity container.

    If the container does not exist, nothing will happen.
    """
    logging.info(f"Stopping Docker container ({container})...")

    try:
        container.stop()
    except Exception:
        pass
    try:
        container.remove()
    except Exception:
        pass
