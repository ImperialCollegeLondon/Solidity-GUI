"""Module for the Component dataclass."""

from dataclasses import dataclass


@dataclass
class Component:
    """Definition of a Component that should be created within a system geometry.

    Attributes:
      shape: name of the shape to use for this component
      label: unique label to apply to this component
      kwargs: function arguments to pass to the shape constructor
    """

    shape: str
    label: str
    kwargs: dict[str, float | list[float]]
