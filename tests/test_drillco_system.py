"""Tests for the drillco_system module."""
import numpy as np

from solidity_gui.main.condition import ConditionAssignmentDatastore, ConditionDatastore
from solidity_gui.main.drillco_system import (
    DRILLCO_CONDITION_ASSIGNMENTS,
    DRILLCO_CONDITIONS,
    DRILLCO_INITIAL_CONDITION_ASSIGNMENTS,
    DRILLCO_INITIAL_CONDITIONS,
    DRILLCO_MATERIAL_ASSIGNMENTS,
    DRILLCO_MATERIALS,
    GAP_LENGTH,
    Condition,
    ConditionAssignment,
    MaterialAssignment,
    create_drillco_system,
)
from solidity_gui.main.geometry import Geometry, GeometryWrapper
from solidity_gui.main.initial_condition import (
    InitialCondition,
    InitialConditionAssignment,
    InitialConditionAssignmentDatastore,
    InitialConditionDatastore,
)
from solidity_gui.main.material import MaterialAssignmentDatastore, MaterialDatastore
from solidity_gui.main.solidity_file_generator import get_template_data


def _mesher(name, component):
    with Geometry() as geom:
        wrapper = GeometryWrapper(geom)
        return wrapper.add_component(component, 0.4)


PARAMETERS = dict(
    bit=dict(width=1.0, length=5.0, inserts=dict(length=0.5, width=0.5)),
    piston=dict(length_ratio=1.5, width=1.5),
)


def test_create_drillco_system():
    """Test create_drillco_system function."""
    (
        meshes,
        materials,
        material_assignments,
        conditions,
        condition_assignments,
        initial_conditions,
        initial_condition_assignments,
    ) = create_drillco_system(PARAMETERS, _mesher)

    # do basic checks of meshes from the created geometry
    ground_mesh = meshes["ground"]
    ground_maxes = ground_mesh.points.max(axis=0)
    ground_mins = ground_mesh.points.min(axis=0)
    assert np.isclose(ground_maxes, (2, 1, 1)).all()
    assert np.isclose(ground_mins, (0, -1, -1)).all()

    bit_mesh = meshes["bit"]
    bit_maxes = bit_mesh.points.max(axis=0)
    bit_mins = bit_mesh.points.min(axis=0)
    bit_width = PARAMETERS["bit"]["width"]
    assert np.isclose(
        bit_maxes - bit_mins,
        (
            PARAMETERS["bit"]["length"] + PARAMETERS["bit"]["inserts"]["length"],
            bit_width,
            bit_width,
        ),
    ).all()

    piston_mesh = meshes["piston"]
    piston_maxes = piston_mesh.points.max(axis=0)
    piston_mins = piston_mesh.points.min(axis=0)
    piston_width = PARAMETERS["piston"]["width"]
    assert np.isclose(
        piston_maxes - piston_mins,
        (
            PARAMETERS["bit"]["length"] * PARAMETERS["piston"]["length_ratio"],
            piston_width,
            piston_width,
        ),
    ).all()
    assert np.isclose(np.abs(piston_maxes[0] - bit_mins[0]), GAP_LENGTH)

    # check material and condition datastructures have been created correctly
    assert materials.keys() == DRILLCO_MATERIALS.keys()
    assert [condition.name for condition in conditions] == list(
        DRILLCO_CONDITIONS.keys()
    )
    for condition, (condition_name, condition_data) in zip(
        conditions, DRILLCO_CONDITIONS.items()
    ):
        assert condition == Condition(name=condition_name, properties=condition_data)
    for initial_condition, (name, data) in zip(
        initial_conditions, DRILLCO_INITIAL_CONDITIONS.items()
    ):
        assert initial_condition == InitialCondition(name=name, properties=data)

    for material_assignment, (material_name, cell_set_name) in zip(
        material_assignments, DRILLCO_MATERIAL_ASSIGNMENTS
    ):
        assert material_assignment == MaterialAssignment(
            material=materials[material_name], cell_set_name=cell_set_name
        )

    for condition_assignment, (condition_id, cell_set_name) in zip(
        condition_assignments, DRILLCO_CONDITION_ASSIGNMENTS
    ):
        assert condition_assignment == ConditionAssignment(
            condition=conditions[condition_id], cell_set_name=cell_set_name
        )
    for initial_condition_assignment, (initial_condition_id, cell_set_name) in zip(
        initial_condition_assignments, DRILLCO_INITIAL_CONDITION_ASSIGNMENTS
    ):
        assert initial_condition_assignment == InitialConditionAssignment(
            initial_condition=initial_conditions[initial_condition_id],
            cell_set_name=cell_set_name,
        )


def test_solidity_input_integration():
    """Integration test checking we can get the Y3D file data for the Drillco system."""
    (
        meshes,
        materials,
        material_assignments,
        conditions,
        condition_assignments,
        initial_conditions,
        initial_condition_assignments,
    ) = create_drillco_system(PARAMETERS, _mesher)
    surface_nodes = {mesh_name: np.array([]) for mesh_name in meshes}

    material_datastore = MaterialDatastore("materials")
    for material in materials.values():
        material_datastore.add(material)
    material_assignment_datastore = MaterialAssignmentDatastore("material_assignments")
    for material_assignment in material_assignments:
        material_assignment_datastore.add(material_assignment)

    condition_datastore = ConditionDatastore("conditions")
    for condition in conditions:
        condition_datastore.add(condition)
    condition_assignment_datastore = ConditionAssignmentDatastore(
        "condition_assignments"
    )
    for condition_assignment in condition_assignments:
        condition_assignment_datastore.add(condition_assignment)

    initial_condition_datastore = InitialConditionDatastore("initial_conditions")
    for initial_condition in initial_conditions:
        initial_condition_datastore.add(initial_condition)
    initial_condition_assignment_datastore = InitialConditionAssignmentDatastore(
        "initial_condition_assignments"
    )
    for initial_condition_assignment in initial_condition_assignments:
        initial_condition_assignment_datastore.add(initial_condition_assignment)

    # just check that we can get the template data without raising any validation errors
    get_template_data(
        meshes,
        material_datastore,
        material_assignment_datastore,
        condition_datastore,
        condition_assignment_datastore,
        initial_condition_datastore,
        initial_condition_assignment_datastore,
        surface_nodes,
    )
