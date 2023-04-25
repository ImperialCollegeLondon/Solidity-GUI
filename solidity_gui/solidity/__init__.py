"""A module for interfacing with the Solidity command-line utility.

It achieves this by using the docker image.
"""
import os.path
import shutil
from tempfile import TemporaryDirectory

from python_on_whales import docker


def run(
    y3d_file_path: str,
    layout_file_path: str,
    pellet_file_path: str,
    materials_file_path: str,
) -> None:
    """Run Solidity with the required command-line arguments.

    Descriptions of arguments are taken from the manual.

    Example:
        run("BST.Y3D", "layout.txt", "pellet.txt", "mat.txt")

    Args:
        y3d_file_path: Path to Y3D file
        layout_file_path: Path to file with format for elements and particles
                          (layout.txt)
        pellet_file_path: Path to file with elements and particles (pellet.txt)
        materials_file_path: Path to materials file (mat.txt)
    """
    with TemporaryDirectory() as tmp:
        shutil.copyfile(y3d_file_path, os.path.join(tmp, "file1.Y3D"))
        shutil.copyfile(layout_file_path, os.path.join(tmp, "file2.txt"))
        shutil.copyfile(pellet_file_path, os.path.join(tmp, "file3.txt"))
        shutil.copyfile(materials_file_path, os.path.join(tmp, "file4.txt"))

        docker.run(
            "ghcr.io/imperialcollegelondon/solidity_project_dev:Solidity_RCS",
            [
                "DEMPlus",
                "/home/software/solidity/run/file1.Y3D",
                "/home/software/solidity/run/file2.txt",
                "/home/software/solidity/run/file3.txt",
                "/home/software/solidity/run/file4.txt",
            ],
            volumes=[(tmp, "/home/software/solidity/run")],
        )
