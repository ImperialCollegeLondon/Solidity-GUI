"""A module for interfacing with the Solidity command-line utility.

It achieves this by using the docker image.
"""
import logging
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Any

from python_on_whales import docker

from ..config import (
    SOLIDITY_DOCKER_IMAGE,
    SOLIDITY_LAYOUT_FILE_NAME,
    SOLIDITY_MATERIALS_FILE_NAME,
    SOLIDITY_PELLET_FILE_NAME,
    SOLIDITY_Y3D_FILE_NAME,
)


def run_solidity(
    y3d_file_path: Path,
    layout_file_path: Path,
    pellet_file_path: Path,
    materials_file_path: Path,
    docker_image: str = SOLIDITY_DOCKER_IMAGE,
) -> None:
    """Run Solidity using the specified input files.

    All the input files must be in the same directory as one another.

    Args:
        y3d_file_path: Path to Y3D file (BST.Y3D)
        layout_file_path: Path to file with format for elements and particles
                          (layout.txt)
        pellet_file_path: Path to file with elements and particles (pellet.txt)
        materials_file_path: Path to materials file (mat.txt)
        docker_image: URL and tag/SHA of docker image

    Raises:
        ValueError: If input files are not in same directory
        RuntimeError: If any of the input files do not exist
    """
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
    docker.run(
        docker_image,
        [
            "DEMPlus",
            str(path_on_container / y3d_file_path.name),
            str(path_on_container / layout_file_path.name),
            str(path_on_container / pellet_file_path.name),
            str(path_on_container / materials_file_path.name),
        ],
        volumes=[(input_files_path.absolute(), str(path_on_container))],
    )


class SolidityContainer(TemporaryDirectory):
    """Provides a container for running the Solidity executable via docker.

    Before run() is called, the Y3D file, layout file, pellet file and materials file
    must all have been saved into the correct paths.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create a new SolidityContainer."""
        # By default, ignore errors when trying to delete temporary files
        if "ignore_cleanup_errors" not in kwargs:
            kwargs["ignore_cleanup_errors"] = True

        super().__init__(*args, **kwargs)
        self._input_files_path = Path(self.name)

    def _file_path(self, filename: str) -> Path:
        return self._input_files_path / filename

    @property
    def y3d_file_path(self) -> Path:
        """Path to Y3D file (BST.Y3D)."""
        return self._file_path(SOLIDITY_Y3D_FILE_NAME)

    @property
    def layout_file_path(self) -> Path:
        """Path to file with format for elements and particles (layout.txt)."""
        return self._file_path(SOLIDITY_LAYOUT_FILE_NAME)

    @property
    def pellet_file_path(self) -> Path:
        """Path to file with elements and particles (pellet.txt)."""
        return self._file_path(SOLIDITY_PELLET_FILE_NAME)

    @property
    def materials_file_path(self) -> Path:
        """Path to materials file (mat.txt)."""
        return self._file_path(SOLIDITY_MATERIALS_FILE_NAME)

    def run(self) -> None:
        """Invoke Solidity with the input files."""
        run_solidity(
            self.y3d_file_path,
            self.layout_file_path,
            self.pellet_file_path,
            self.materials_file_path,
        )
