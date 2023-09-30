"""Tests for the solidity_file_generator module."""
import itertools

import numpy as np
import pytest

from solidity_gui.main.components import Component
from solidity_gui.main.condition import (
    Condition,
    ConditionAssignment,
    ConditionAssignmentDatastore,
    ConditionDatastore,
)
from solidity_gui.main.geometry import Geometry
from solidity_gui.main.geometry_wrapper import GeometryWrapper
from solidity_gui.main.initial_condition import (
    InitialCondition,
    InitialConditionAssignment,
    InitialConditionAssignmentDatastore,
    InitialConditionDatastore,
)
from solidity_gui.main.material import (
    PROPERTIES,
    Material,
    MaterialAssignment,
    MaterialDatastore,
)
from solidity_gui.main.meshes import get_cell_offset
from solidity_gui.main.solidity_file_generator import (
    SystemValidationError,
    check_unassigned_nodes,
    fetch_condition_assignments,
    fetch_material_assignments,
    generate_elements_data,
    generate_interactions_data,
    generate_material_data,
    generate_nodes_data,
    generate_surface_elements_data,
    get_tetra_side_lengths,
)


def _get_mesh_and_surface_nodes(component, label):
    with Geometry() as geom:
        wrapper = GeometryWrapper(geom, label)
        mesh = wrapper.add_component(component)
        surface_nodes = wrapper.get_surface_nodes()
    return mesh, surface_nodes


def test_generate_nodes_data():
    """Test generate_nodes_data function."""
    mesh_a, surface_nodes_a = _get_mesh_and_surface_nodes(
        Component(shape="ball", kwargs=dict(center=[0, 0, 0], radius=1)), "a"
    )
    mesh_b, surface_nodes_b = _get_mesh_and_surface_nodes(
        Component(shape="box", kwargs=dict(x0=[2, 2, 2], extents=[1, 1, 1])), "b"
    )

    meshes = dict(a=mesh_a, b=mesh_b)
    surface_nodes = dict(a=surface_nodes_a, b=surface_nodes_b)

    # choose a mix of cell sets to apply conditions to
    cell_set_names = ["a_volume_0", "b_volume_0", "b_surface_1"]

    conditions = ConditionDatastore(
        "conditions", {i: Condition(name=str(i)) for i in range(len(cell_set_names))}
    )
    condition_assignments = ConditionAssignmentDatastore(
        "condition_assigments",
        {
            i: ConditionAssignment(conditions[i], cell_set_name)
            for i, cell_set_name in enumerate(cell_set_names)
        },
    )

    velocity = (0.0, 1.5, 2.0)
    initial_conditions = InitialConditionDatastore(
        "initial_conditions",
        {
            0: InitialCondition(
                name="a", properties=dict(x=velocity[0], y=velocity[1], z=velocity[2])
            )
        },
    )
    initial_condition_assignments = InitialConditionAssignmentDatastore(
        "initial_condition_assignments",
        {
            0: InitialConditionAssignment(
                initial_conditions[0], cell_set_name="a_volume_0"
            )
        },
    )

    data = generate_nodes_data(
        meshes,
        surface_nodes,
        conditions,
        condition_assignments,
        initial_conditions,
        initial_condition_assignments,
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

    # check that all conditions have been used
    assigned_condition_ids = np.unique(data["node_conditions"])
    for i in range(len(conditions)):
        assert i in assigned_condition_ids

    mesh_a_node_ids = np.arange(mesh_a.points.shape[0])
    assert all(data["node_conditions"][mesh_a_node_ids] == 0)
    mesh_b_surface_1_node_ids = (
        np.unique(
            mesh_b.cells_dict["triangle"][
                mesh_b.cell_sets_dict["b_surface_1"]["triangle"]
                - get_cell_offset(mesh_b.cells_dict, "triangle")
            ].flatten()
        )
        + mesh_a.points.shape[0]
    )
    assert all(data["node_conditions"][mesh_b_surface_1_node_ids] == 2)

    mesh_b_other_node_ids = np.setdiff1d(
        np.arange(data["num_nodes"]),
        np.concatenate((mesh_a_node_ids, mesh_b_surface_1_node_ids)),
    )
    assert all(data["node_conditions"][mesh_b_other_node_ids] == 1)

    # check initial conditions assigned only to mesh a
    mesh_b_node_ids = np.arange(mesh_b.points.shape[0]) + mesh_a_node_ids.shape[0]
    assert (
        data["node_initial_conditions"][mesh_a_node_ids] == np.array(velocity)
    ).all()
    assert (
        data["node_initial_conditions"][mesh_b_node_ids] == np.array((0.0, 0.0, 0.0))
    ).all()


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
    target_data["_calculated"] = dict(
        is_joint=[13, 13, 15], is_fracture=[0, 3, 0], material_index=[1, 2, 2]
    )

    assert data["num_materials"] == 3
    assert data["material_properties"] == target_data


def _count_tetras(mesh):
    return mesh.cells_dict["tetra"].data.shape[0]


def test_generate_elements_data():
    """Test generate_elements_data function."""
    mesh_a, surface_nodes_a = _get_mesh_and_surface_nodes(
        Component(shape="box", kwargs=dict(x0=[0, 0, 0], extents=[1, 1, 1])), label="a"
    )
    mesh_b, surface_nodes_b = _get_mesh_and_surface_nodes(
        Component(shape="box", kwargs=dict(x0=[2, 2, 2], extents=[1, 1, 1])), label="b"
    )

    meshes = dict(a=mesh_a, b=mesh_b)
    surface_nodes = dict(a=surface_nodes_a, b=surface_nodes_b)
    materials = MaterialDatastore(
        "materials", {i: Material(name=str(i)) for i in range(len(meshes))}
    )
    assignments1 = {
        0: MaterialAssignment(materials[0], "a_volume_0"),
    }
    assignments2 = {
        1: MaterialAssignment(materials[1], "b_volume_0"),
    }

    # We should get errors if some of the elements don't have assigned materials
    with pytest.raises(SystemValidationError):
        generate_elements_data(meshes, materials, assignments1, surface_nodes)
    with pytest.raises(SystemValidationError):
        generate_elements_data(meshes, materials, assignments2, surface_nodes)

    data = generate_elements_data(
        meshes, materials, assignments1 | assignments2, surface_nodes
    )

    assert data["points_per_tetra"] == 4

    num_tetras = (_count_tetras(mesh_a), _count_tetras(mesh_b))
    total_tetras = sum(num_tetras)
    assert data["num_tetra"] == total_tetras

    assert np.all(data["cell_materials"][: num_tetras[0]] == 0)
    assert np.all(data["cell_materials"][num_tetras[0] :] == 1)

    # There is probably a better test we can do for this...
    assert data["tetra_node_ids"].shape == (total_tetras, 5)


def test_generate_interactions_data():
    """Test generate_interactions_data function."""
    mesh_a, surface_nodes_a = _get_mesh_and_surface_nodes(
        Component(shape="ball", kwargs=dict(center=[0, 0, 0], radius=1)), label="a"
    )
    mesh_b, surface_nodes_b = _get_mesh_and_surface_nodes(
        Component(shape="box", kwargs=dict(x0=[2, 2, 2], extents=[1, 1, 1])), label="b"
    )

    meshes = dict(a=mesh_a, b=mesh_b)

    data = generate_interactions_data(meshes)

    # Calculate expected values based on input meshes
    tetra_side_lengths = get_tetra_side_lengths(meshes)
    expected_min_length = np.min(tetra_side_lengths)
    expected_mean_length = np.mean(tetra_side_lengths)

    assert data["min_length"] == expected_min_length
    assert data["mean_length"] == expected_mean_length


def test_fetch_material_assignments_non_contiguous_ids():
    """Check function where materials have non-contiguous id values."""
    mesh, _ = _get_mesh_and_surface_nodes(
        Component(shape="ball", kwargs=dict(center=[0, 0, 0], radius=1)), label="a"
    )
    materials = MaterialDatastore("materials", {2: Material(name="1")})
    material_assignments = {
        1: MaterialAssignment(material=materials[2], cell_set_name="a_volume_0"),
    }

    element_assignments = fetch_material_assignments(
        mesh, materials, material_assignments
    )
    # values in the second column should be indexes into the material property columns
    # not the key of the material datastore
    assert np.setdiff1d(element_assignments[:, 1], (0, 1)).size == 0


def test_fetch_condition_assignments():
    """Test fetch_condition_assignments function."""
    mesh_a, surface_nodes_a = _get_mesh_and_surface_nodes(
        Component(shape="ball", kwargs=dict(center=[0, 0, 0], radius=1)), label="a"
    )
    conditions = ConditionDatastore(
        "conditions", {0: Condition(name="0"), 1: Condition(name="1")}
    )
    condition_assignment1 = ConditionAssignment(conditions[0], "a_surface_0")
    condition_assignment2 = ConditionAssignment(conditions[1], "a_volume_0")

    condition_assigments = ConditionAssignmentDatastore(
        "assigments", {0: condition_assignment1, 1: condition_assignment2}
    )

    node_conditions = fetch_condition_assignments(
        mesh_a, conditions, condition_assigments
    )

    assert np.all(np.isin(node_conditions[:, 1], [0, 1, 2]))


def test_fetch_condition_assignments_non_contiguous_ids():
    """Check function where conditions have non-contiguous id values."""
    mesh, _ = _get_mesh_and_surface_nodes(
        Component(shape="ball", kwargs=dict(center=[0, 0, 0], radius=1)), label="a"
    )

    conditions = ConditionDatastore(
        "conditions", {0: Condition(name="1"), 2: Condition(name="2")}
    )

    condition_assignments = ConditionAssignmentDatastore(
        "condition_assignments",
        {
            0: ConditionAssignment(
                condition=conditions[0], cell_set_name="a_surface_0"
            ),
            1: ConditionAssignment(condition=conditions[2], cell_set_name="a_volume_0"),
        },
    )

    element_assignments = fetch_condition_assignments(
        mesh, conditions, condition_assignments
    )
    # values in the second column should be indexes into the condition columns
    # not the actual value of condition_id datastore
    assert np.setdiff1d(element_assignments[:, 1], (0, 1)).size == 0


def test_check_unassigned_nodes():
    """Test check_unassigned_nodes function."""
    mesh_a, surface_nodes_a = _get_mesh_and_surface_nodes(
        Component(shape="ball", kwargs=dict(center=[0, 0, 0], radius=1)), label="a"
    )
    conditions = ConditionDatastore("conditions", {0: Condition(name="0")})
    condition_assignment1 = ConditionAssignment(conditions[0], "a_surface_0")
    condition_assignments = ConditionAssignmentDatastore(
        "assigments", {0: condition_assignment1}
    )
    node_conditions = fetch_condition_assignments(
        mesh_a, conditions, condition_assignments
    )
    # We should get an error if there are unassigned nodes
    with pytest.raises(SystemValidationError):
        check_unassigned_nodes(node_conditions, mesh_a)


def test_generate_surface_elements_data():
    """Test generate_surface_elements_data function."""
    mesh_a, surface_nodes_a = _get_mesh_and_surface_nodes(
        Component(shape="ball", kwargs=dict(center=[0, 0, 0], radius=1)), label="a"
    )
    mesh_b, surface_nodes_b = _get_mesh_and_surface_nodes(
        Component(shape="box", kwargs=dict(x0=[2, 2, 2], extents=[1, 1, 1])), label="b"
    )

    meshes = dict(a=mesh_a, b=mesh_b)

    surface_elements_data = generate_surface_elements_data(meshes)

    assert surface_elements_data["points_per_triangle"] == 3
    assert (
        surface_elements_data["num_triangles"]
        == mesh_a.cells_dict["triangle"].data.shape[0]
        + mesh_b.cells_dict["triangle"].data.shape[0]
    )
    assert surface_elements_data["triangle_node_ids"].shape == (
        surface_elements_data["num_triangles"],
        3,
    )
