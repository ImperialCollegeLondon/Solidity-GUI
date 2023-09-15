"""Module defining Condition and ConditionAssignment datastructures."""
from dataclasses import dataclass, field

from marshmallow import validate
from meshio import Mesh
from pubsub import pub

from .datastore import IndexDatastore
from .forms import Form
from .forms.fields import FloatField, IntField, StrField
from .meshes import mesh_datastore

one_or_zero = validate.Range(min=0, max=1)


class ConditionForm(Form):
    """Form for collecting condition data."""

    name = StrField(display_name="Name")
    acceleration_x = FloatField(display_name="Acceleration X")
    acceleration_y = FloatField(display_name="Acceleration Y")
    acceleration_z = FloatField(display_name="Acceleration Z")
    force_x = FloatField(display_name="Force X")
    force_y = FloatField(display_name="Force Y")
    force_z = FloatField(display_name="Force Z")
    velocity_x = FloatField(display_name="Velocity X")
    velocity_y = FloatField(display_name="Velocity Y")
    velocity_z = FloatField(display_name="Velocity Z")
    velocity_constraint_x = IntField(
        display_name="Velocity Constraint X", validators=[one_or_zero]
    )
    velocity_constraint_y = IntField(
        display_name="Velocity Constraint Y", validators=[one_or_zero]
    )
    velocity_constraint_z = IntField(
        display_name="Velocity Constraint Z", validators=[one_or_zero]
    )


Properties_Dict_Type = dict[str, float]


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
    ) -> dict[str, list[ConditionAssignment]]:
        """Returns all ConditionAssignments associated with a particular mesh."""
        assignments: dict[str, list[ConditionAssignment]] = dict()
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
