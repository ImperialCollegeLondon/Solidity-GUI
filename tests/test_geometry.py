"""Tests for geometry module."""

from solidity_gui.main.geometry import Component, generate_mesh

RESOLUTION = 0.2


def check_mesh_cell_sets(mesh, no_surfaces, label):
    """Helper function that checks the cell sets of a mesh are correct."""
    assert len(mesh.cell_sets.keys()) == no_surfaces + 1
    assert mesh.cell_sets[f"{label}_volume"][2] is not None
    for i in range(no_surfaces):
        assert mesh.cell_sets[f"{label}_surface_{i}"][1] is not None


def test_ball():
    """Test creation of a ball."""
    label = "globe"
    mesh = generate_mesh(
        [Component(shape="ball", args=[(0, 0, 0), 1], label=label)], RESOLUTION
    )
    check_mesh_cell_sets(mesh, 1, label)


def test_box():
    """Test creation of a box."""
    label = "cube"
    mesh = generate_mesh(
        [Component(shape="box", args=[(0, 0, 0), (1, 1, 1)], label=label)], RESOLUTION
    )
    check_mesh_cell_sets(mesh, 6, label)


def test_cone():
    """Test creation of a cone."""
    label = "conical"
    mesh = generate_mesh(
        [Component(shape="cone", args=[(0, 0, 0), (1, 1, 1), 1, 0], label=label)],
        RESOLUTION,
    )
    check_mesh_cell_sets(mesh, 2, label)


def test_cylinder():
    """Test creation of a cylinder."""
    label = "cylindrical"
    mesh = generate_mesh(
        [Component(shape="cylinder", args=[(0, 0, 0), (1, 1, 1), 1], label=label)],
        RESOLUTION,
    )
    check_mesh_cell_sets(mesh, 3, label)


def test_multiple():
    """Test creating both a box and a ball at the same time."""
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
