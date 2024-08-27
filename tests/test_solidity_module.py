"""Tests for the Solidity module."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from solidity_gui.config import SOLIDITY_CONTAINER_NAME
from solidity_gui.solidity import run_solidity_no_stream

INPUT_DIR = Path(__file__).parent.absolute() / "solidity_input_files"
INPUT_FILES = [
    INPUT_DIR / f for f in ("BST.Y3D", "layout.txt", "pellet.txt", "mat.txt")
]


@patch("solidity_gui.solidity._pull_image_sync")
@patch("solidity_gui.solidity.docker")
def test_run_solidity_no_error(docker_mock: Mock, pull_mock: Mock) -> None:
    """Test that run_solidity() passes the correct args to the docker wrapper."""
    image = MagicMock()
    pull_mock.return_value = image
    run_solidity_no_stream(
        INPUT_FILES[0], INPUT_FILES[1], INPUT_FILES[2], INPUT_FILES[3], 1
    )
    pull_mock.assert_called_once_with()

    RUN_DIR = "/home/software/solidity/run"
    docker_mock.run.assert_called_once_with(
        image,
        [
            "DEMPlus",
            f"{RUN_DIR}/BST.Y3D",
            f"{RUN_DIR}/layout.txt",
            f"{RUN_DIR}/pellet.txt",
            f"{RUN_DIR}/mat.txt",
        ],
        volumes=[(INPUT_DIR, RUN_DIR)],
        detach=True,
        stream=False,
        name=SOLIDITY_CONTAINER_NAME,
        envs={"OMP_NUM_THREADS": "1"},
        cpus=1,
    )


@pytest.mark.parametrize("missing_idx", range(4))
def test_run_solidity_missing_file(missing_idx: int) -> None:
    """Test that run_solidity() raises an error if an input file is missing."""
    files = INPUT_FILES.copy()
    files[missing_idx] = INPUT_DIR / "madeup.txt"

    with patch("solidity_gui.solidity.docker"):
        with pytest.raises(RuntimeError):
            run_solidity_no_stream(files[0], files[1], files[2], files[3], 1)


@pytest.mark.parametrize("diff_idx", range(4))
def test_run_solidity_diff_dir(diff_idx: int) -> None:
    """Test that run_solidity() raises an error if input files are in different dirs."""
    files = INPUT_FILES.copy()
    files[diff_idx] = Path(".") / files[diff_idx].name

    with patch("solidity_gui.solidity.docker"):
        with pytest.raises(ValueError):
            run_solidity_no_stream(files[0], files[1], files[2], files[3], 1)
