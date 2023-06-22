"""Tests for the solidity_file_generator module."""
import itertools

import numpy as np
import pytest

from solidity_gui.main.condition import ConditionAssignment
from solidity_gui.main.geometry import Component, Geometry, GeometryWrapper
from solidity_gui.main.material import PROPERTIES, Material, MaterialAssignment
from solidity_gui.main.solidity_file_generator import (
    SystemValidationError,
    fetch_condition_assignments,
    generate_elements_data,
    generate_interactions_data,
    generate_material_data,
    generate_nodes_data,
    get_tetra_side_lengths,
)


def _get_mesh_and_surface_nodes(component):
    with Geometry() as geom:
        wrapper = GeometryWrapper(geom)
        mesh = wrapper.add_component(component, 0.2)
        surface_nodes = wrapper.get_surface_nodes()
    return mesh, surface_nodes


def test_generate_nodes_data():
    """Test generate_nodes_data function."""
    mesh_a, surface_nodes_a = _get_mesh_and_surface_nodes(
        Component(shape="ball", label="a", kwargs=dict(center=[0, 0, 0], radius=1))
    )
    mesh_b, surface_nodes_b = _get_mesh_and_surface_nodes(
        Component(shape="box", label="b", kwargs=dict(x0=[2, 2, 2], extents=[1, 1, 1]))
    )

    meshes = dict(a=mesh_a, b=mesh_b)
    surface_nodes = dict(a=surface_nodes_a, b=surface_nodes_b)

    data = generate_nodes_data(
        meshes, surface_nodes, {0: ConditionAssignment(0, "a_volume")}
    )

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


def test_generate_material_data():
    """Test generate_material_data function."""
    material1 = Material(name="material_1")
    material2 = Material(name="material_2")

    counter = itertools.count(0.0)
    for property_ in material2.properties.values():
        property_.enabled = True
        property_.data = {key: next(counter) for key in property_.default_data}

    data = generate_material_data({0: material1, 1: material2})

    counter = itertools.count(0.0)

    target_data = {
        property_label: {
            key: [value] + [next(counter)] * 2
            for key, value in property_.default_data.items()
        }
        for property_label, property_ in PROPERTIES().items()
    }
    target_data["_calculated"] = dict(is_joint=[13, 13, 15], is_fracture=[0, 3, 0])

    assert data["num_materials"] == 3
    assert data["material_properties"] == target_data


def _count_tetras(mesh):
    return mesh.cells_dict["tetra"].data.shape[0]


def test_generate_elements_data():
    """Test generate_elements_data function."""
    mesh_a, surface_nodes_a = _get_mesh_and_surface_nodes(
        Component(shape="box", label="a", kwargs=dict(x0=[0, 0, 0], extents=[1, 1, 1]))
    )
    mesh_b, surface_nodes_b = _get_mesh_and_surface_nodes(
        Component(shape="box", label="b", kwargs=dict(x0=[2, 2, 2], extents=[1, 1, 1]))
    )

    meshes = dict(a=mesh_a, b=mesh_b)
    assignments1 = {
        0: MaterialAssignment(0, "a_volume"),
    }
    assignments2 = {
        1: MaterialAssignment(1, "b_volume"),
    }

    # We should get errors if some of the elements don't have assigned materials
    with pytest.raises(SystemValidationError):
        generate_elements_data(meshes, assignments1)
    with pytest.raises(SystemValidationError):
        generate_elements_data(meshes, assignments2)

    data = generate_elements_data(meshes, assignments1 | assignments2)

    assert data["points_per_tetra"] == 4

    num_tetras = (_count_tetras(mesh_a), _count_tetras(mesh_b))
    total_tetras = sum(num_tetras)
    assert data["num_tetra"] == total_tetras

    assert np.all(data["cell_materials"][: num_tetras[0]] == 0)
    # The material for the second mesh is offset by the number of tetras in the first
    # plus one
    assert np.all(data["cell_materials"][num_tetras[0] + 1 :] == num_tetras[0] + 1)

    # There is probably a better test we can do for this...
    assert data["tetra_node_ids"].shape == (total_tetras, 5)


def test_generate_interactions_data():
    """Test generate_interactions_data function."""
    mesh_a, surface_nodes_a = _get_mesh_and_surface_nodes(
        Component(shape="ball", label="a", kwargs=dict(center=[0, 0, 0], radius=1))
    )
    mesh_b, surface_nodes_b = _get_mesh_and_surface_nodes(
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


def test_fetch_condition_assignments():
    """Test fetch_condition_assignments function."""
    mesh_a, surface_nodes_a = _get_mesh_and_surface_nodes(
        Component(shape="ball", label="a", kwargs=dict(center=[0, 0, 0], radius=1))
    )

    condition_assignment1 = ConditionAssignment(0, "a_surface_0")
    condition_assignment2 = ConditionAssignment(1, "a_volume")

    node_conditions = fetch_condition_assignments(
        mesh_a, {0: condition_assignment1, 1: condition_assignment2}
    )

    assert np.all(np.isin(node_conditions[:, 1], [0, 1, 2]))
