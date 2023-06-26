"""A dialog for creating a DrillCo system geometry."""
from typing import Any

import meshio
import numpy as np
from marshmallow import validate
from pubsub import pub

from .forms import Form, NestedForm, SimpleFormDialog
from .forms.fields import FloatField, IntField
from .geometry import Component
from .gmsh_process import GmshProcess, gmsh_process_datastore
from .meshes import DEFAULT_RESOLUTION

GAP_LENGTH = 0.5
"""Length of gap between system components."""
INSERT_DISPLACEMENT_FACTOR = 0.5
"""Distance of inserts from bit center as a factor of the radius of the bit."""
INSERT_LENGTH_FACTOR = 1.25
"""Length of bit inserts as a factor of the bit face height."""
BIT_FACE_HEIGHT = 0.25
"""Height of the domed drill bit cap."""
SYSTEM_AXIS = np.array([1, 0, 0])
"""Arbitrary axis for system orientation"""
GAP_VECTOR = SYSTEM_AXIS * GAP_LENGTH
"""Vector added to space out system components."""


class InsertForm(Form):
    """Data for drill bit inserts."""

    number = IntField(validators=[validate.Range(min=1)])
    width = FloatField(validators=[validate.Range(min=0, min_inclusive=False)])


class BitForm(Form):
    """Data for drill bits."""

    width = FloatField(validators=[validate.Range(min=0, min_inclusive=False)])
    length = FloatField(validators=[validate.Range(min=0, min_inclusive=False)])
    inserts = NestedForm(InsertForm)


class PistonForm(Form):
    """Data for piston."""

    length_ratio = FloatField(validators=[validate.Range(min=0, min_inclusive=False)])
    width = FloatField(validators=[validate.Range(min=0, min_inclusive=False)])


class DrillCoForm(Form):
    """Form containing parameters for the DrillCo system geometry."""

    bit = NestedForm(BitForm)
    piston = NestedForm(PistonForm)


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
        super().__init__(DrillCoForm, **kwargs)
        self.setWindowTitle("Create DrillCo System Geometry")

    def _ok_clicked(self) -> None:
        if data := super()._ok_clicked():
            pub.sendMessage(
                "add_component.finish",
                mesh_name="ground",
                obj=_create_mesh(
                    "ground",
                    Component("box", "ground", dict(x0=[0, -1, -1], extents=[2, 2, 2])),
                ),
            )

            bit_axis = SYSTEM_AXIS * data["bit"]["length"]
            bit_x0 = (
                -SYSTEM_AXIS * (data["bit"]["length"] + BIT_FACE_HEIGHT) - GAP_VECTOR
            )
            bit_radius = data["bit"]["width"] / 2
            pub.sendMessage(
                "add_component.finish",
                mesh_name="bit",
                obj=_create_mesh(
                    "bit",
                    Component(
                        "drillbit",
                        "bit",
                        dict(
                            insert_number=data["bit"]["inserts"]["number"],
                            x0=list(bit_x0),
                            axis=list(bit_axis),
                            face_height=BIT_FACE_HEIGHT,
                            radius=bit_radius,
                            insert_radius=data["bit"]["inserts"]["width"] / 2,
                            insert_displacement=bit_radius * INSERT_DISPLACEMENT_FACTOR,
                            insert_length=BIT_FACE_HEIGHT * INSERT_LENGTH_FACTOR,
                        ),
                    ),
                ),
            )

            piston_axis = (
                SYSTEM_AXIS * data["bit"]["length"] * data["piston"]["length_ratio"]
            )
            piston_x0 = bit_x0 - piston_axis - GAP_VECTOR
            pub.sendMessage(
                "add_component.finish",
                mesh_name="piston",
                obj=_create_mesh(
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
                ),
            )
            self.close()
