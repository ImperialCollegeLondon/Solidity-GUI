"""Tests for the solidity_file_generator module."""

import numpy as np

from solidity_gui.main.geometry import Component, Geometry, GeometryWrapper
from solidity_gui.main.solidity_file_generator import (
    generate_nodes_data,
    generate_interactions_data,
    get_tetra_side_lengths,
)


def _get_mesh_and_surface_nodes(component):
    with Geometry() as geom:
        wrapper = GeometryWrapper(geom)
        mesh = wrapper.add_component(component, 0.2)
        surface_nodes = wrapper.get_surface_nodes()
    return mesh, surface_nodes


def _get_mesh(component):
    with Geometry() as geom:
        wrapper = GeometryWrapper(geom)
        mesh = wrapper.add_component(component, 0.2)
    return mesh


def test_generate_nodes_data():
    """Test get_template_data function."""
    mesh_a, surface_nodes_a = _get_mesh_and_surface_nodes(
        Component(shape="ball", label="a", kwargs=dict(center=[0, 0, 0], radius=1))
    )
    mesh_b, surface_nodes_b = _get_mesh_and_surface_nodes(
        Component(shape="box", label="b", kwargs=dict(x0=[2, 2, 2], extents=[1, 1, 1]))
    )

    meshes = dict(a=mesh_a, b=mesh_b)
    surface_nodes = dict(a=surface_nodes_a, b=surface_nodes_b)

    data = generate_nodes_data(meshes, surface_nodes)

    assert data["num_timesteps"] == 2000000
    assert data["num_nodes"] == mesh_a.points.shape[0] + mesh_b.points.shape[0]
    assert data["nodes"].shape == (data["num_nodes"], 3)
    assert np.all(
        data["nodes"] == np.concatenate([mesh_a.points, mesh_b.points], axis=0)
    )

    # build a boolean filter to check that all surface nodes have a flag value of 1
    # and others 0
    combined_surface_node_indices = np.concatenate(
        [surface_nodes_a, surface_nodes_b + mesh_a.points.shape[0]]
    )
    surface_node_filter = np.full(data["num_nodes"], False)
    surface_node_filter[combined_surface_node_indices] = True
    surface_node_flags = data["surface_node_flags"]
    assert surface_node_flags.shape == (data["num_nodes"],)
    assert np.all(surface_node_flags[surface_node_filter] == 1)
    assert np.all(surface_node_flags[np.logical_not(surface_node_filter)] == 0)


def test_generate_interactions_data():
    """Test generate_interactions_data function."""
    mesh_a = _get_mesh(
        Component(shape="ball", label="a", kwargs=dict(center=[0, 0, 0], radius=1))
    )
    mesh_b = _get_mesh(
        Component(shape="box", label="b", kwargs=dict(x0=[2, 2, 2], extents=[1, 1, 1]))
    )

    meshes = dict(a=mesh_a, b=mesh_b)

    data = generate_interactions_data(meshes)

    # Calculate expected values based on input meshes
    tetra_side_lengths = get_tetra_side_lengths(meshes)
    expected_min_length = np.min(tetra_side_lengths)
    expected_mean_length = np.mean(tetra_side_lengths)

    assert data["min_length"] == expected_min_length
    assert data["mean_length"] == expected_mean_length
