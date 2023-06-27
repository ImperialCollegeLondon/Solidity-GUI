"""Module defining Condition and ConditionAssignment datastructures."""
from dataclasses import dataclass, field
from typing import Dict, List, Type

from meshio import Mesh
from pubsub import pub

from .datastore import IndexDatastore
from .meshes import mesh_datastore

Attributes_Dict_Type = Dict[str, Type[float] | bool]


Properties_Dict_Type = Dict[str, float]


def PROPERTIES() -> Properties_Dict_Type:
    """Define the dictionary of available properties for a Condition."""
    return {
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
    }


@dataclass
class Condition:
    """Definition of a Condition.

    Attributes:
        name: name of this condition
        properties: dictionary containing all properties for this Condition
    """

    name: str
    properties: Properties_Dict_Type = field(default_factory=PROPERTIES)


@dataclass(frozen=True)
class ConditionAssignment:
    """Simple datastructure recording the association of a cell_set and Condition."""

    condition: Condition
    cell_set_name: str


class ConditionDatastore(IndexDatastore[Condition]):
    """Convenience IndexDatastore subclass with concretised type."""


class ConditionAssignmentDatastore(IndexDatastore[ConditionAssignment]):
    """Datastore for ConditionAssignments."""

    def get_assignments_for_mesh(
        self, mesh: Mesh
    ) -> Dict[str, List[ConditionAssignment]]:
        """Returns all ConditionAssignments associated with a particular mesh."""
        assignments: Dict[str, List[ConditionAssignment]] = dict()
        for assignment in self.values():
            if assignment.cell_set_name in mesh.cell_sets:
                # should only ever be one cell type in a cell set
                cell_type = list(mesh.cell_sets_dict[assignment.cell_set_name].keys())[
                    0
                ]
                assignments.setdefault(cell_type, []).append(assignment)
        return assignments


condition_datastore = ConditionDatastore("conditions")
condition_assignment_datastore = ConditionAssignmentDatastore("condition_assignments")


def sync_assignments_condition_removed(key: int, value: Condition) -> None:
    """Message handler sync assignment datastore when condition datastore changes."""
    for assignment_key, assignment in condition_assignment_datastore.items():
        if assignment.condition == value:
            del condition_assignment_datastore[assignment_key]


def sync_assignments_mesh_removed(key: int, value: Mesh) -> None:
    """Message handler sync assignment datastore when mesh datastore changes."""
    for assignment_key, assignment in condition_assignment_datastore.items():
        for cell_set_name in value.cell_sets:
            if assignment.cell_set_name == cell_set_name:
                del condition_assignment_datastore[assignment_key]
                break


pub.subscribe(sync_assignments_condition_removed, condition_datastore.remove_topic)
pub.subscribe(sync_assignments_mesh_removed, mesh_datastore.remove_topic)
