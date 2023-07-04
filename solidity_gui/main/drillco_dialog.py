"""A dialog for creating a DrillCo system geometry."""
from typing import Any, Dict

import meshio
from marshmallow import ValidationError, validate
from pubsub import pub

from .condition import condition_assignment_datastore, condition_datastore
from .drillco_system import create_drillco_system
from .forms import Form, NestedForm, SimpleFormDialog
from .forms.fields import FloatField
from .geometry import Component
from .gmsh_process import GmshProcess, gmsh_process_datastore
from .material import material_assignment_datastore, material_datastore
from .meshes import DEFAULT_RESOLUTION


class InsertForm(Form):
    """Data for drill bit inserts."""

    width = FloatField(validators=[validate.Range(min=0, min_inclusive=False, max=5)])
    length = FloatField(validators=[validate.Range(min=0, min_inclusive=False, max=1)])


class BitForm(Form):
    """Data for drill bits."""

    width = FloatField(validators=[validate.Range(min=0, min_inclusive=False, max=5)])
    length = FloatField(validators=[validate.Range(min=0, min_inclusive=False, max=10)])
    inserts = NestedForm(InsertForm)

    def validate(self, data: Dict[str, Any], **kwargs: Any) -> None:
        """Schema level validator."""
        if data["inserts"]["width"] > data["width"]:
            raise ValidationError("Insert cannot be wider than bit.")


class PistonForm(Form):
    """Data for piston."""

    width = FloatField(validators=[validate.Range(min=0, min_inclusive=False, max=5)])
    length = FloatField(validators=[validate.Range(min=0, min_inclusive=False, max=10)])


class GroundForm(Form):
    """Data for ground."""

    width = FloatField(validators=[validate.Range(min=0, min_inclusive=False, max=5)])
    height = FloatField(validators=[validate.Range(min=0, min_inclusive=False, max=3)])


class DrillCoForm(Form):
    """Form containing parameters for the DrillCo system geometry."""

    bit = NestedForm(BitForm)
    piston = NestedForm(PistonForm)
    ground = NestedForm(GroundForm)


def _create_mesh(mesh_name: str, component: Component) -> meshio.Mesh:
    """Helper function to synchronously create meshes."""
    try:
        gmsh_process = gmsh_process_datastore[mesh_name]
    except KeyError:
        gmsh_process = GmshProcess(mesh_name)
        gmsh_process.start()
        gmsh_process_datastore[mesh_name] = gmsh_process

    return gmsh_process.call_function(
        "add_component", component=component, resolution=DEFAULT_RESOLUTION
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
                piston=dict(length=0.26, width=0.0265),
                bit=dict(
                    length=0.265, width=0.03, inserts=dict(width=0.02, length=0.005)
                ),
                ground=dict(width=0.250, height=0.15),
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
        self.close()
