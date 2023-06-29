"""Tests for the drillco_system module."""
import numpy as np

from solidity_gui.main.drillco_system import (
    BIT_FACE_HEIGHT,
    DRILLCO_CONDITION_ASSIGNMENTS,
    DRILLCO_CONDITIONS,
    DRILLCO_MATERIAL_ASSIGNMENTS,
    DRILLCO_MATERIALS,
    GAP_LENGTH,
    INSERT_LENGTH_FACTOR,
    Condition,
    ConditionAssignment,
    MaterialAssignment,
    create_drillco_system,
)
from solidity_gui.main.geometry import Geometry, GeometryWrapper


def _mesher(name, component):
    with Geometry() as geom:
        wrapper = GeometryWrapper(geom)
        return wrapper.add_component(component, 0.4)


def test_create_drillco_system():
    """Test create_drillco_system function."""
    parameters = dict(
        bit=dict(width=1.0, length=5.0, inserts=dict(number=2, width=0.15)),
        piston=dict(length_ratio=1.5, width=1.5),
    )
    (
        meshes,
        materials,
        material_assignments,
        conditions,
        condition_assignments,
    ) = create_drillco_system(parameters, _mesher)

    # do basic checks of meshes from the created geometry
    ground_mesh = meshes["ground"]
    ground_maxes = ground_mesh.points.max(axis=0)
    ground_mins = ground_mesh.points.min(axis=0)
    assert np.isclose(ground_maxes, (2, 1, 1)).all()
    assert np.isclose(ground_mins, (0, -1, -1)).all()

    bit_mesh = meshes["bit"]
    bit_maxes = bit_mesh.points.max(axis=0)
    bit_mins = bit_mesh.points.min(axis=0)
    bit_width = parameters["bit"]["width"]
    insert_height = BIT_FACE_HEIGHT * INSERT_LENGTH_FACTOR
    assert np.isclose(
        bit_maxes - bit_mins,
        (
            parameters["bit"]["length"] + insert_height,
            bit_width,
            bit_width,
        ),
    ).all()

    piston_mesh = meshes["piston"]
    piston_maxes = piston_mesh.points.max(axis=0)
    piston_mins = piston_mesh.points.min(axis=0)
    piston_width = parameters["piston"]["width"]
    assert np.isclose(
        piston_maxes - piston_mins,
        (
            parameters["bit"]["length"] * parameters["piston"]["length_ratio"],
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
