import copy
from dataclasses import dataclass, field
from meshio import Mesh
from typing import Dict, Type
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
    }


@dataclass
class Condition:
    """Definition of a Condition.

    Attributes:
        name: name of this condition
        properties: dictionary containing all properties for this Condition
    """

    name: str
    properties: Properties_Dict_Type = field(
        default_factory=lambda: copy.deepcopy(PROPERTIES())
    )


@dataclass(frozen=True)
class ConditionAssignment:
    """Simple datastructure recording the association of a cell_set and Condition."""

    condition_id: int
    cell_set_name: str


class ConditionDatastore(IndexDatastore[Condition]):
    """Convenience IndexDatastore subclass with concretised type."""


condition_datastore = ConditionDatastore("conditions")
condition_assignment_datastore: IndexDatastore[ConditionAssignment] = IndexDatastore(
    "condition_assignment"
)


def sync_assignments_condition_removed(key: int, value: Condition) -> None:
    """Message handler sync assignment datastore when condition datastore changes."""
    for assignment_key, assignment in list(condition_assignment_datastore.items()):
        if assignment.condition_id == key:
            del condition_assignment_datastore[assignment_key]


def sync_assignments_mesh_removed(key: int, value: Mesh) -> None:
    """Message handler sync assignment datastore when mesh datastore changes."""
    for assignment_key, assignment in list(condition_assignment_datastore.items()):
        for cell_set_name in value.cell_sets:
            if assignment.cell_set_name == cell_set_name:
                del condition_assignment_datastore[assignment_key]
                break


pub.subscribe(sync_assignments_condition_removed, condition_datastore.remove_topic)
pub.subscribe(sync_assignments_mesh_removed, mesh_datastore.remove_topic)
