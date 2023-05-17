"""Tests for the Solidity module."""
from pathlib import Path, PurePosixPath
from unittest.mock import Mock, patch

import pytest

from solidity_gui.solidity import SolidityContainer, run_solidity

INPUT_DIR = Path(__file__).parent.absolute() / "solidity_input_files"
INPUT_FILES = [
    INPUT_DIR / f for f in ("BST.Y3D", "layout.txt", "pellet.txt", "mat.txt")
]


@pytest.fixture
def container() -> SolidityContainer:
    """Provides a SolidityContainer()."""
    return SolidityContainer()


@patch("solidity_gui.solidity.docker")
def test_run_solidity_no_error(docker_mock: Mock) -> None:
    """Test that run_solidity() passes the correct args to the docker wrapper."""
    run_solidity(*INPUT_FILES)

    RUN_DIR = "/home/software/solidity/run"
    docker_mock.run.assert_called_once_with(
        "ghcr.io/imperialcollegelondon/solidity_project_dev:Solidity_RCS",
        [
            "DEMPlus",
            f"{RUN_DIR}/BST.Y3D",
            f"{RUN_DIR}/layout.txt",
            f"{RUN_DIR}/pellet.txt",
            f"{RUN_DIR}/mat.txt",
        ],
        volumes=[(INPUT_DIR, PurePosixPath(RUN_DIR))],
    )


@pytest.mark.parametrize("missing_idx", range(4))
def test_run_solidity_missing_file(missing_idx: int) -> None:
    """Test that run_solidity() raises an error if an input file is missing."""
    files = INPUT_FILES.copy()
    files[missing_idx] = INPUT_DIR / "madeup.txt"

    with pytest.raises(RuntimeError):
        run_solidity(*files)


@pytest.mark.parametrize("diff_idx", range(4))
def test_run_solidity_diff_dir(diff_idx: int) -> None:
    """Test that run_solidity() raises an error if input files are in different dirs."""
    files = INPUT_FILES.copy()
    files[diff_idx] = Path(".") / files[diff_idx].name

    with pytest.raises(ValueError):
        run_solidity(*files)


@pytest.mark.parametrize(
    "prop,filename",
    (
        ("y3d_file_path", "BST.Y3D"),
        ("layout_file_path", "layout.txt"),
        ("pellet_file_path", "pellet.txt"),
        ("materials_file_path", "mat.txt"),
    ),
)
def test_solidity_container_file_paths(
    prop: str, filename: str, container: SolidityContainer
) -> None:
    """Test SolidityContainer's file paths."""
    assert getattr(container, prop) == container._input_files_path / filename


@patch("solidity_gui.solidity.run_solidity")
def test_solidity_container_run(run_mock: Mock, container: SolidityContainer) -> None:
    """Test SolidityContainer's run() method."""
    container.run()
    run_mock.assert_called_once_with(
        container.y3d_file_path,
        container.layout_file_path,
        container.pellet_file_path,
        container.materials_file_path,
    )
