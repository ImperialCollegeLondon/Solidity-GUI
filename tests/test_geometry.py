"""Tests for geometry module."""

from random import random

import numpy as np
from sklearn.decomposition import PCA

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


def angle_between_vectors(a, b):
    """Return the angle between `a` and `b`."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return np.arccos(np.dot(a, b) / (norm_a * norm_b))


def test_dome():
    """Test creation of a dome and the geometric properties of the resulting mesh.

    The dome shape goes beyond simply wrapping a built-in geometry generation function
    of gmsh and therefore we do some more involved tests to check that actually
    generated mesh has appropriate geometry properties.
    """
    label = "lid"
    base_radius = 1

    # generate random axis vector for dome
    # the 'height' of the dome must be more than 2x the radius in order for the PCA
    # based analysis below to work
    theta = random() * np.pi
    phi = random() * np.pi * 2
    r = base_radius * 4
    axis = [
        r * np.sin(theta) * np.cos(phi),
        r * np.sin(theta) * np.sin(phi),
        r * np.cos(theta),
    ]

    mesh = generate_mesh(
        [Component(shape="dome", args=[(0, 0, 0), axis, base_radius], label=label)],
        RESOLUTION,
    )

    # use principle component analysis to find orientation of primary axis
    pca = PCA()
    pca.fit(mesh.points)

    # first principle component should closely match axis
    assert abs(angle_between_vectors(pca.components_[0], axis)) <= np.pi / 100

    check_mesh_cell_sets(mesh, 2, label)


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
