"""A module for interfacing with the Solidity command-line utility.

It achieves this by using the docker image.
"""
from pathlib import Path, PosixPath
from tempfile import TemporaryDirectory

from python_on_whales import docker


class SolidityContainer:
    """Provides a container for running the Solidity executable via docker.

    Before run() is called, the Y3D file, layout file, pellet file and materials file
    must all have been saved into input_files_path.
    """

    Y3D_FILE_NAME = "BST.Y3D"
    LAYOUT_FILE_NAME = "layout.txt"
    PELLET_FILE_NAME = "pellet.txt"
    MATERIALS_FILE_NAME = "materials.txt"

    def __init__(self) -> None:
        """Create a new SolidityContainer."""
        self._tmp_dir = TemporaryDirectory(ignore_cleanup_errors=True)
        self.input_files_path = Path(self._tmp_dir.name)

    @property
    def y3d_file_path(self) -> Path:
        """Path to Y3D file (BST.Y3D)."""
        return self.input_files_path / self.Y3D_FILE_NAME

    @property
    def layout_file_path(self) -> Path:
        """Path to file with format for elements and particles (layout.txt)."""
        return self.input_files_path / self.LAYOUT_FILE_NAME

    @property
    def pellet_file_path(self) -> Path:
        """Path to file with elements and particles (pellet.txt)."""
        return self.input_files_path / self.PELLET_FILE_NAME

    @property
    def materials_file_path(self) -> Path:
        """Path to materials file (mat.txt)."""
        return self.input_files_path / self.MATERIALS_FILE_NAME

    def run(self) -> None:
        """Run Solidity using the files in input_files_path as inputs."""
        path_on_container = PosixPath("/home/software/solidity/run")
        docker.run(
            "ghcr.io/imperialcollegelondon/solidity_project_dev:Solidity_RCS",
            [
                "DEMPlus",
                str(path_on_container / self.Y3D_FILE_NAME),
                str(path_on_container / self.LAYOUT_FILE_NAME),
                str(path_on_container / self.PELLET_FILE_NAME),
                str(path_on_container / self.MATERIALS_FILE_NAME),
            ],
            volumes=[(self.input_files_path, str(path_on_container))],
        )
