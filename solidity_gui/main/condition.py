"""Module defining Condition and ConditionAssignment datastructures."""

from dataclasses import dataclass, field

from marshmallow import validate
from meshio import Mesh
from pubsub import pub

from .assignment_base import AssignmentBase
from .datastore import IndexDatastore
from .forms import Form
from .forms.fields import ComboBoxField, FloatField, StrField
from .meshes import mesh_datastore

one_or_zero = validate.Range(min=0, max=1)


class ConditionForm(Form):
    """Form for collecting condition data."""

    constraint_values = ["Force", "Acceleration", "Velocity"]

    name = StrField(display_name="Name", validators=[validate.Length(min=1, max=20)])
    constraint_x = ComboBoxField(items=constraint_values, display_name="Constraint X")
    x_value = FloatField(display_name="X Value")
    constraint_y = ComboBoxField(items=constraint_values, display_name="Constraint Y")
    y_value = FloatField(display_name="Y Value")
    constraint_z = ComboBoxField(items=constraint_values, display_name="Constraint Z")
    z_value = FloatField(display_name="Z Value")


Properties_Dict_Type = dict[str, float | str]


def PROPERTIES() -> Properties_Dict_Type:
    """Define the dictionary of available properties for a Condition."""
    return {
        "x_value": 0.0,
        "y_value": 0.0,
        "z_value": 0.0,
        "constraint_x": "Force",
        "constraint_y": "Force",
        "constraint_z": "Force",
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


@dataclass
class ConditionAssignment(AssignmentBase):
    """Simple datastructure recording the association of a cell_set and Condition."""

    condition: Condition


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
    keys_to_delete = []
    for assignment_key, assignment in condition_assignment_datastore.items():
        for cell_set_name in value.cell_sets:
            if assignment.cell_set_name == cell_set_name:
                keys_to_delete.append(assignment_key)
                break
    for key in keys_to_delete:
        del condition_assignment_datastore[key]


pub.subscribe(sync_assignments_condition_removed, condition_datastore.remove_topic)
pub.subscribe(sync_assignments_mesh_removed, mesh_datastore.remove_topic)
