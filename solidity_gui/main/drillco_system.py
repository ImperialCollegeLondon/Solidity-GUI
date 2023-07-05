"""Controller components for creating drillco systems."""
from typing import Any, Callable, Dict, List, Tuple

import meshio
import numpy as np

from .condition import Condition, ConditionAssignment
from .geometry import Component
from .initial_condition import InitialCondition, InitialConditionAssignment
from .material import Material, MaterialAssignment

GAP_LENGTH = 0.0001
"""Length of gap between system components."""
INSERT_DISPLACEMENT_FACTOR = 0.5
"""Distance of inserts from bit center as a factor of the radius of the bit."""
SYSTEM_AXIS = np.array([1, 0, 0])
"""Arbitrary axis for system orientation"""
GAP_VECTOR = SYSTEM_AXIS * GAP_LENGTH
"""Vector added to space out system components."""

DRILLCO_MATERIALS: Dict[str, Dict[str, Dict[str, object]]] = dict(
    granite=dict(
        density=dict(density=2626.0),
        elasticity=dict(
            lames_first_parameter=2.233251e10, lames_second_parameter=2.419355e10
        ),
        fracture=dict(damage_delta_0=0.005, damage_delta_1=1, damage_threshold=0.5),
        other=dict(
            mass_damping_coefficient=14000,
            penalty_number=3000e9,
            energy_release_rate_mode_1=10.0,
            energy_release_rate_mode_2=1000.0,
            tensile_strength=10.98e6,
            cohesion=29.84e6,
            internal_friction_coefficient=1.85,
            sliding_friction_coefficient=0.6,
            static_friction_coefficient=0.0,
            pressure_friction_coefficient=0.0,
            velocity_factor=0.0,
            pressure_factor=1.0,
            mass_ratio_coefficent=0.1,
        ),
    ),
    steel=dict(
        density=dict(density=7850.0),
        elasticity=dict(
            lames_first_parameter=1.070506e11,
            lames_second_parameter=7.751938e10,
        ),
        other=dict(
            mass_damping_coefficient=20000,
            penalty_number=3000e9,
            energy_release_rate_mode_1=100.0,
            energy_release_rate_mode_2=1000.0,
            tensile_strength=11.4e6,
            cohesion=46.49e6,
            internal_friction_coefficient=0.577,
            sliding_friction_coefficient=0.6,
            static_friction_coefficient=0.0,
            pressure_friction_coefficient=0.0,
            velocity_factor=0.0,
            pressure_factor=1.0,
            mass_ratio_coefficent=1,
        ),
    ),
    carbide=dict(
        density=dict(density=15250.0),
        elasticity=dict(
            lames_first_parameter=1.666667e11,
            lames_second_parameter=2.500000e11,
        ),
        other=dict(
            mass_damping_coefficient=40000,
            penalty_number=3000e9,
            energy_release_rate_mode_1=100.0,
            energy_release_rate_mode_2=1000.0,
            tensile_strength=11.4e6,
            cohesion=46.49e6,
            internal_friction_coefficient=0.577,
            sliding_friction_coefficient=0.6,
            static_friction_coefficient=0.0,
            pressure_friction_coefficient=0.0,
            velocity_factor=0.0,
            pressure_factor=1.0,
            mass_ratio_coefficent=1,
        ),
    ),
)
DRILLCO_MATERIAL_ASSIGNMENTS = (
    ("granite", "ground_volume_0"),
    ("steel", "bit_volume_0"),
    ("carbide", "bit_volume_1"),
    ("steel", "piston_volume_0"),
)
DRILLCO_CONDITIONS = dict(
    condition1={
        "acceleration_x": 0.0,
        "acceleration_y": 0.0,
        "acceleration_z": 0.0,
        "force_x": 0.0,
        "force_y": 0.0,
        "force_z": 0.0,
        "velocity_x": 0.0,
        "velocity_y": 0.0,
        "velocity_z": 0.0,
        "velocity_constraint_x": 0,
        "velocity_constraint_y": 0,
        "velocity_constraint_z": 0,
    },
    condition2={
        "acceleration_x": 0.0,
        "acceleration_y": 0.0,
        "acceleration_z": 0.0,
        "force_x": 0.0,
        "force_y": 0.0,
        "force_z": 0.0,
        "velocity_x": 0.0,
        "velocity_y": 0.0,
        "velocity_z": 0.0,
        "velocity_constraint_x": 1,
        "velocity_constraint_y": 1,
        "velocity_constraint_z": 1,
    },
)

DRILLCO_CONDITION_ASSIGNMENTS = (
    (0, "ground_volume_0"),
    (0, "bit_volume_0"),
    (0, "bit_volume_1"),
    (0, "piston_volume_0"),
    (1, "ground_surface_1"),
)

DRILLCO_INITIAL_CONDITION_CELL_SETS = ["piston_volume_0"]


def _create_and_assign_materials() -> (
    Tuple[Dict[str, Material], List[MaterialAssignment]]
):
    materials = {
        name: Material.from_properties_dict(name, data)
        for name, data in DRILLCO_MATERIALS.items()
    }
    material_assignments = [
        MaterialAssignment(
            material=materials[material_name],
            cell_set_name=cell_set_name,
        )
        for material_name, cell_set_name in DRILLCO_MATERIAL_ASSIGNMENTS
    ]
    return materials, material_assignments


def _create_and_assign_conditions() -> (
    Tuple[List[Condition], List[ConditionAssignment]]
):
    conditions = [
        Condition(name=name, properties=properties)
        for name, properties in DRILLCO_CONDITIONS.items()
    ]
    condition_assignments = [
        ConditionAssignment(condition=conditions[i], cell_set_name=cell_set_name)
        for i, cell_set_name in DRILLCO_CONDITION_ASSIGNMENTS
    ]
    return conditions, condition_assignments


def _create_and_assign_initial_conditions(
    parameters: Dict[str, Any]
) -> Tuple[List[InitialCondition], List[InitialConditionAssignment]]:
    piston_speed = parameters["piston"]["speed"]
    initial_conditions = []
    initial_condition_assignments = []
    for i, cell_set_name in enumerate(DRILLCO_INITIAL_CONDITION_CELL_SETS):
        ic = InitialCondition(name=f"condition{i}")
        ic.properties["x"] = piston_speed
        initial_conditions.append(ic)
        assignment = InitialConditionAssignment(ic, cell_set_name)
        initial_condition_assignments.append(assignment)

    return initial_conditions, initial_condition_assignments


def _create_drillco_geometry(
    data: Dict[str, Any], mesh_generator: Callable[[str, Component, float], meshio.Mesh]
) -> Dict[str, meshio.Mesh]:
    meshes = dict(
        ground=mesh_generator(
            "ground",
            Component(
                "ground",
                "ground",
                dict(
                    x0=[0, 0, 0],
                    axis=SYSTEM_AXIS * data["ground"]["height"],
                    radius=data["ground"]["width"] / 2,
                    contact_point=[0, 0, 0],
                    contact_mesh_size=0.0015,
                ),
            ),
            0.01,
        )
    )

    bit_axis = SYSTEM_AXIS * data["bit"]["length"]
    bit_x0 = (
        -SYSTEM_AXIS * (data["bit"]["length"] + data["bit"]["inserts"]["length"])
        - GAP_VECTOR
    )
    bit_radius = data["bit"]["width"] / 2
    meshes["bit"] = mesh_generator(
        "bit",
        Component(
            "drillbit",
            "bit",
            dict(
                x0=list(bit_x0),
                axis=list(bit_axis),
                radius=bit_radius,
                insert_radius=data["bit"]["inserts"]["width"] / 2,
                insert_length=data["bit"]["inserts"]["length"],
            ),
        ),
        0.005,
    )

    piston_axis = SYSTEM_AXIS * data["piston"]["length"]
    piston_x0 = bit_x0 - piston_axis - GAP_VECTOR

    meshes["piston"] = mesh_generator(
        "piston",
        Component(
            "cylinder",
            "piston",
            dict(
                x0=list(piston_x0),
                axis=list(piston_axis),
                radius=data["piston"]["width"] / 2,
            ),
        ),
        0.005,
    )
    return meshes


def create_drillco_system(
    parameters: Dict[str, Any],
    mesh_generator: Callable[[str, Component, float], meshio.Mesh],
) -> Tuple[
    Dict[str, meshio.Mesh],
    Dict[str, Material],
    List[MaterialAssignment],
    List[Condition],
    List[ConditionAssignment],
    List[InitialCondition],
    List[InitialConditionAssignment],
]:
    """Populate the provided datastores with a Drillco system setup.

    Args:
      parameters: drillco system parameters,
      mesh_generator: function called to create meshes
    """
    meshes = _create_drillco_geometry(parameters, mesh_generator)
    materials, material_assignments = _create_and_assign_materials()
    conditions, condition_assignments = _create_and_assign_conditions()
    (
        initial_conditions,
        initial_condition_assignments,
    ) = _create_and_assign_initial_conditions(parameters)
    return (
        meshes,
        materials,
        material_assignments,
        conditions,
        condition_assignments,
        initial_conditions,
        initial_condition_assignments,
    )
