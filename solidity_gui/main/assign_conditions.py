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

    cell_set_names = []
    for mesh in mesh_datastore.values():
        cell_set_names.extend(list(mesh.cell_sets.keys()))

    condition1 = Condition("Condition 1")
    condition_datastore.add(condition1)
    condition2 = Condition("Condition 2")
    condition2.properties = {property: 1.0 for property in condition2.properties}
    condition_datastore.add(condition2)

    # Since every node requires a condition, we need to assign a condition to every
    # cell set.
    # We do this by assigning the same condition to multiple cell sets.
    for i, cell_set_name in enumerate(cell_set_names):
        condition_assignment = ConditionAssignment(
            condition_id=i % len(condition_datastore),
            cell_set_name=cell_set_name,
        )
        condition_assignment_datastore.add(condition_assignment)
