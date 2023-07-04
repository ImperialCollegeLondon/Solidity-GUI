"""Module defining InitialCondition and InitialConditionAssignment datastructures."""
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
    return {"x": 0.0, "y": 0.0, "z": 0.0}


@dataclass
class InitialCondition:
    """Definition of a InitialCondition.

    Attributes:
        name: name of this initial condition
        properties: dictionary containing all properties for this Condition
    """

    name: str
    properties: Properties_Dict_Type = field(default_factory=PROPERTIES)


@dataclass(frozen=True)
class InitialConditionAssignment:
    """Simple datastructure recording the association of a cell_set and Condition."""

    initial_condition: InitialCondition
    cell_set_name: str


class InitialConditionDatastore(IndexDatastore[InitialCondition]):
    """Convenience IndexDatastore subclass with concretised type."""


class InitialConditionAssignmentDatastore(IndexDatastore[InitialConditionAssignment]):
    """Datastore for ConditionAssignments."""

    def get_assignments_for_mesh(self, mesh: Mesh) -> List[InitialConditionAssignment]:
        """Returns all ConditionAssignments associated with a particular mesh."""
        assignments: List[InitialConditionAssignment] = []
        for assignment in self.values():
            if assignment.cell_set_name in mesh.cell_sets:
                # should only ever be one cell type in a cell set
                cell_type = list(mesh.cell_sets_dict[assignment.cell_set_name].keys())[
                    0
                ]
                if cell_type != "tetra":
                    raise ValueError("Initial Conditions must be assigned to volumes.")
                assignments.append(assignment)
        return assignments


initial_condition_datastore = InitialConditionDatastore("initial_conditions")
initial_condition_assignment_datastore = InitialConditionAssignmentDatastore(
    "initial_condition_assignments"
)


def sync_assignments_initial_condition_removed(
    key: int, value: InitialCondition
) -> None:
    """Message handler sync assignment datastore when condition datastore changes."""
    for assignment_key, assignment in initial_condition_assignment_datastore.items():
        if assignment.initial_condition == value:
            del initial_condition_assignment_datastore[assignment_key]


def sync_assignments_mesh_removed(key: int, value: Mesh) -> None:
    """Message handler sync assignment datastore when mesh datastore changes."""
    for assignment_key, assignment in initial_condition_assignment_datastore.items():
        for cell_set_name in value.cell_sets:
            if assignment.cell_set_name == cell_set_name:
                del initial_condition_assignment_datastore[assignment_key]
                break


pub.subscribe(
    sync_assignments_initial_condition_removed, initial_condition_datastore.remove_topic
)
pub.subscribe(sync_assignments_mesh_removed, mesh_datastore.remove_topic)
