"""Creation and manipulation of system geometries."""

import warnings
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import gmsh
import numpy as np
import pygmsh
from marshmallow import ValidationError, validate
from pygmsh.common.dummy import Dummy

from .forms import Form
from .forms.fields import FloatField, VectorField

Vector = tuple[float, float, float]


class Surface(pygmsh.common.surface.Surface):
    """Generates a Surface from CurveLoop.

    This class includes a necessary bug fix when working with the OCC geometry kernel.
    Raised with pygmsh project - https://github.com/meshpro/pygmsh/issues/567. If this
    issue is resolved this class can be removed.
    """

    def __init__(
        self,
        env: gmsh.model.geo | gmsh.model.occ,
        curve_loop: pygmsh.common.curve_loop.CurveLoop,
    ):
        """Create a new Surface instance.

        Args:
          env: gmsh interface to either the built-in or OCC geometry kernel
          curve_loop: contains all the Line objects for the loop construction
        """
        assert isinstance(curve_loop, pygmsh.common.curve_loop.CurveLoop)
        self.curve_loop = curve_loop
        self.num_edges = len(curve_loop)
        self._id = env.addSurfaceFilling(self.curve_loop._id)  # fixed line
        self.dim_tag = (2, self._id)
        self.dim_tags = [self.dim_tag]


class Geometry(pygmsh.occ.Geometry):
    """Interface to gmsh geometry functionality.

    This version of the Geometry interface updates the `add_surface` method to use a
    custom Surface class in order circumvent issue #567 of meshpro/pymsh.
    """

    def add_surface(self, *args: Any, **kwargs: Any) -> Surface:
        """Add a new surface to the geometry."""
        return Surface(self.env, *args, **kwargs)

    def boolean_union(
        self,
        entities: list[Dummy],
        delete_first: bool = True,
        delete_other: bool = True,
    ) -> list[Dummy]:
        """Perform a boolean union of geometric entities.

        A thin wrapper around pygmsh.occ.Geometry that suppresses warnings.
        """
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message=".*Specified mesh size.*", module=".*geometry"
            )
            return super().boolean_union(entities, delete_first, delete_other)

    def boolean_fragments(
        self,
        d0: Dummy,
        d1: Dummy,
        delete_first: bool = True,
        delete_other: bool = True,
    ) -> list[Dummy]:
        """Perform a boolean union of geometric entities.

        A thin wrapper around pygmsh.occ.Geometry that suppresses warnings.
        """
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message=".*Specified mesh size.*", module=".*geometry"
            )
            return super().boolean_fragments(d0, d1, delete_first, delete_other)


@dataclass
class Shape:
    """Definition of a shape.

    Contains the information required by ShapeFactory to build a shape using the
    pygmsh.occ.Geometry class.

    Attributes:
      name: name of the shape e.g. "box"
      method: method that is called to create a shape instance
      args: mapping of method arguments to expected types
    """

    name: str
    method: Callable
    form: type[Form]


greater_than_zero = validate.Range(min=0, min_inclusive=False)


class BoxForm(Form):
    """Form defining data required for box shape creation."""

    x0 = VectorField(display_name="Corner Coordinates")
    extents = VectorField(
        display_name="Side Lengths",
        description="Length of box sides in x, y and z dimensions.",
        validators=[validate.NoneOf([0.0])],
    )


class BallForm(Form):
    """Form defining data required for ball shape creation."""

    center = VectorField(display_name="Center Coordinates")
    radius = FloatField(
        description="The radius of the ball.",
        validators=[greater_than_zero],
    )


def non_zero_magnitude(vector: list[float], **kwargs: Any) -> None:
    """Validate vector data has a magnitude greater than zero.

    Args:
      vector: vector data
      **kwargs: additional keyword arguments passed to Marshmallow validators
    """
    if np.linalg.norm(vector) == 0.0:
        raise ValidationError("Vector must have non-zero magnitude.")


class ConeForm(Form):
    """Form defining data required for cone shape creation."""

    center = VectorField(display_name="Base Center Coordinates")
    axis = VectorField(
        display_name="Axis Vector", vector_validators=[non_zero_magnitude]
    )
    radius0 = FloatField(
        display_name="Base Radius",
        validators=[greater_than_zero],
    )
    radius1 = FloatField(
        display_name="Tip Radius",
        validators=[validate.Range(min=0, min_inclusive=True)],
    )

    def validate(self, data: dict[str, Any], **kwargs: Any) -> None:
        """Schema level validator."""
        if data["radius1"] >= data["radius0"]:
            raise ValidationError("Base radius must be larger than tip radius.")


class CylinderForm(Form):
    """Form defining data required for cylinder shape creation."""

    x0 = VectorField(display_name="Base Center Coordinates")
    axis = VectorField(
        display_name="Axis Vector", vector_validators=[non_zero_magnitude]
    )
    radius = FloatField(validators=[greater_than_zero])


SHAPES = dict(
    box=Shape(name="box", method=pygmsh.occ.geometry.Geometry.add_box, form=BoxForm),
    ball=Shape(name="ball", method=pygmsh.occ.Geometry.add_ball, form=BallForm),
    cone=Shape(name="cone", method=pygmsh.occ.Geometry.add_cone, form=ConeForm),
    cylinder=Shape(
        name="cylinder", method=pygmsh.occ.Geometry.add_cylinder, form=CylinderForm
    ),
)
"""Library of supported shapes."""
