"""A dialog for creating a DrillCo system geometry."""
from typing import Any, Dict

import meshio
from marshmallow import ValidationError, validate
from pubsub import pub

from .condition import condition_assignment_datastore, condition_datastore
from .control import control_datastore
from .drillco_system import create_drillco_system
from .forms import Form, NestedForm, SimpleFormDialog
from .forms.fields import FloatField, IntField
from .forms.widgets import DoubleSpinBoxWidget
from .geometry import Component
from .gmsh_process import GmshProcess, gmsh_process_datastore
from .initial_condition import (
    initial_condition_assignment_datastore,
    initial_condition_datastore,
)
from .material import material_assignment_datastore, material_datastore

INSERT_MIN_WIDTH, INSERT_MAX_WIDTH = 0.01, 0.045
INSERT_MIN_LENGTH, INSERT_MAX_LENGTH = 0.005, 0.02
BIT_MIN_WIDTH, BIT_MAX_WIDTH = 0.015, 0.045
BIT_MIN_LENGTH, BIT_MAX_LENGTH = 0.13, 0.39
PISTON_MIN_WIDTH, PISTON_MAX_WIDTH = 0.013, 0.039
PISTON_MIN_LENGTH, PISTON_MAX_LENGTH = 0.13, 0.39
GROUND_MIN_WIDTH, GROUND_MAX_WIDTH = 0.125, 0.375
GROUND_MIN_HEIGHT, GROUND_MAX_HEIGHT = 0.075, 0.225


class WiderFloatField(FloatField):
    """FloatField with widget providing more decimals."""

    _default_widget = DoubleSpinBoxWidget(decimals=5)


class EvenWiderFloatField(FloatField):
    """FloatField with widget providing even more decimals."""

    _default_widget = DoubleSpinBoxWidget(decimals=15)


class InsertForm(Form):
    """Data for drill bit inserts."""

    width = WiderFloatField(
        validators=[validate.Range(min=INSERT_MIN_WIDTH, max=INSERT_MAX_WIDTH)]
    )
    length = WiderFloatField(
        validators=[validate.Range(min=INSERT_MIN_LENGTH, max=INSERT_MAX_LENGTH)]
    )


class BitForm(Form):
    """Data for drill bits."""

    width = WiderFloatField(
        validators=[validate.Range(min=BIT_MIN_WIDTH, max=BIT_MAX_WIDTH)]
    )
    length = WiderFloatField(
        validators=[validate.Range(min=BIT_MIN_LENGTH, max=BIT_MAX_LENGTH)]
    )
    inserts = NestedForm(InsertForm)

    def validate(self, data: Dict[str, Any], **kwargs: Any) -> None:
        """Schema level validator."""
        if data["inserts"]["width"] > data["width"]:
            raise ValidationError("Insert cannot be wider than bit.")


class PistonForm(Form):
    """Data for piston."""

    width = WiderFloatField(
        validators=[validate.Range(min=PISTON_MIN_WIDTH, max=PISTON_MAX_WIDTH)]
    )
    length = WiderFloatField(
        validators=[validate.Range(min=PISTON_MIN_LENGTH, max=PISTON_MAX_LENGTH)]
    )
    speed = FloatField(
        display_name="Impact Speed",
        validators=[validate.Range(min=0, min_inclusive=False)],
    )


class GroundForm(Form):
    """Data for ground."""

    width = WiderFloatField(
        validators=[validate.Range(min=GROUND_MIN_WIDTH, max=GROUND_MAX_WIDTH)]
    )
    height = WiderFloatField(
        validators=[validate.Range(min=GROUND_MIN_HEIGHT, max=GROUND_MAX_HEIGHT)]
    )


class DrillCoGeometryForm(Form):
    """Form containing parameters for the DrillCo system geometry."""

    bit = NestedForm(BitForm)
    piston = NestedForm(PistonForm)
    ground = NestedForm(GroundForm)


class DrillCoControlForm(Form):
    """Form collecting simulation control parameters."""

    num_timesteps = IntField(display_name="Number of Timesteps")
    time_step_size = EvenWiderFloatField(
        display_name="Size of Timestep", validators=[validate.Range(min=0, max=1)]
    )


class DrillCoForm(Form):
    """Form collecting drillco system parameters."""

    geometry = NestedForm(DrillCoGeometryForm)
    control = NestedForm(DrillCoControlForm)


def _create_mesh(
    mesh_name: str, component: Component, resolution: float
) -> meshio.Mesh:
    """Helper function to synchronously create meshes."""
    try:
        gmsh_process = gmsh_process_datastore[mesh_name]
    except KeyError:
        gmsh_process = GmshProcess(mesh_name)
        gmsh_process.start()
        gmsh_process_datastore[mesh_name] = gmsh_process

    return gmsh_process.call_function(
        "add_component", component=component, resolution=resolution
    )


class DrillCoDialog(SimpleFormDialog):
    """A dialog displaying and processing DrillCoForm."""

    def __init__(self, **kwargs: Any):
        """Create a new DrillCoDialog.

        Args:
          kwargs: passed to superclass constructor
        """
        super().__init__(
            DrillCoForm,
            initial_data=dict(
                geometry=dict(
                    piston=dict(length=0.26, width=0.0265),
                    bit=dict(
                        length=0.265, width=0.03, inserts=dict(width=0.02, length=0.005)
                    ),
                    ground=dict(width=0.250, height=0.15),
                ),
                control=dict(
                    num_timesteps=2000000,
                    time_step_size=2.45000000000e-09,
                ),
            ),
            **kwargs,
        )
        self.setWindowTitle("Create DrillCo System Geometry")

    def _ok_clicked(self) -> None:
        if not (data := super()._ok_clicked()):
            return

        (
            meshes,
            materials,
            material_assignments,
            conditions,
            condition_assignments,
            initial_conditions,
            initial_condition_assignments,
            simulation_control_parameters,
        ) = create_drillco_system(data, _create_mesh)

        for mesh_name, mesh in meshes.items():
            pub.sendMessage("add_component.finish", mesh_name=mesh_name, obj=mesh)
        for material in materials.values():
            material_datastore.add(material)
        for material_assignment in material_assignments:
            material_assignment_datastore.add(material_assignment)
        for condition in conditions:
            condition_datastore.add(condition)
        for condition_assignment in condition_assignments:
            condition_assignment_datastore.add(condition_assignment)
        for initial_condition in initial_conditions:
            initial_condition_datastore.add(initial_condition)
        for initial_condition_assignment in initial_condition_assignments:
            initial_condition_assignment_datastore.add(initial_condition_assignment)
        control_datastore.update(simulation_control_parameters)
        self.close()
