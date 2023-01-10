"""A module for interfacing with the Solidity command-line utility.

It achieves this by using the docker image.
"""
import os.path
import shutil
from tempfile import TemporaryDirectory

from python_on_whales import docker


def run(filepath1: str, filepath2: str, filepath3: str, filepath4: str) -> None:
    """Run Solidity with the four required command-line arguments.

    Example:
        run("BST.Y3D", "layout.txt", "pellet.txt", "mat.txt")

    Todo:
        Find out what these arguments mean so that we can give them better names.
    """
    with TemporaryDirectory() as tmp:
        shutil.copyfile(filepath1, os.path.join(tmp, "file1.Y3D"))
        shutil.copyfile(filepath2, os.path.join(tmp, "file2.txt"))
        shutil.copyfile(filepath3, os.path.join(tmp, "file3.txt"))
        shutil.copyfile(filepath4, os.path.join(tmp, "file4.txt"))

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
