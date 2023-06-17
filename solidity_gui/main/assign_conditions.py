"""Assign conditions to cell sets."""
from .condition import (
    Condition,
    ConditionAssignment,
    condition_assignment_datastore,
    condition_datastore,
)
from .meshes import mesh_datastore


def assign_conditions() -> None:
    """Assign conditions to cell sets."""
    mesh = list(mesh_datastore.values())[0]
    cell_sets = mesh.cell_sets
    cell_set_names = list(cell_sets.keys())

    condition1 = Condition("Condition 1")
    condition_datastore.add(condition1)
    condition_assignment = ConditionAssignment(
        condition_id=0,
        cell_set_name=cell_set_names[0],
    )
    condition_assignment_datastore.add(condition_assignment)
    condition2 = Condition("Condition 2")
    condition2.properties = {property: 1.0 for property in condition2.properties}
    condition_datastore.add(condition2)
    condition_assignment = ConditionAssignment(
        condition_id=1,
        cell_set_name=cell_set_names[1],
    )
    condition_assignment_datastore.add(condition_assignment)
