"""Tests for geometry module."""

from solidity_gui.main.geometry import Component, generate_mesh

RESOLUTION = 0.2


def test_ball():
    """Test creation of a ball."""
    label = "globe"
    mesh = generate_mesh(
        [Component(shape="ball", args=[(0, 0, 0), 1], label=label)], RESOLUTION
    )
    assert len(mesh.cell_sets.keys()) == 2
    assert mesh.cell_sets[f"{label}_volume"][2] is not None
    assert mesh.cell_sets[f"{label}_surface_0"][1] is not None


def test_box():
    """Test creation of a box."""
    label = "cube"
    mesh = generate_mesh(
        [Component(shape="box", args=[(0, 0, 0), (1, 1, 1)], label=label)], RESOLUTION
    )
    assert len(mesh.cell_sets.keys()) == 7
    assert mesh.cell_sets[f"{label}_volume"][2] is not None
    for i in range(6):
        assert mesh.cell_sets[f"{label}_surface_{i}"][1] is not None


def test_both():
    """Test creating both a box and a ball."""
    box_label = "cube"
    ball_label = "globe"
    mesh = generate_mesh(
        [
            Component(shape="box", args=[(0, 0, 0), (1, 1, 1)], label=box_label),
            Component(shape="ball", args=[(0, 0, 0), 1], label=ball_label),
        ],
        RESOLUTION,
    )
    assert len(mesh.cell_sets.keys()) == 9
