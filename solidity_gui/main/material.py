"""Module containing definitions for bundling material and properties data."""

from dataclasses import dataclass, field
from typing import Dict, Type

Attributes_Dict_Type = Dict[str, Type[float] | bool]


@dataclass
class Property:
    """Definition of a Property.

    Each Material instance has a properties attribute which contains
    all the available properties defined in PROPERTIES().
    In theory a given Material could use all of these properties but,
    they can be switched on or off using the enabled attribute.

    Attributes:
        name: name of this property
        category: name of the category which this property appears under
        enabled: bool stating whether this property is enabled for its Material
        attributes: attributes pertaining to this property
    """

    name: str
    category: str
    enabled: bool
    attributes: Attributes_Dict_Type


Properties_Dict_Type = dict[str, Property]


def PROPERTIES() -> Properties_Dict_Type:
    """Define the dictionary of available properties for a Material."""
    return {
        "density": Property(
            category="General",
            name="Density",
            enabled=False,
            args=dict(density=float),
        ),
        "mohr_coulomb": Property(
            category="Mechanical",
            name="Mohr-Coulomb",
            enabled=False,
            args=dict(specify_tension_cutoff=bool),
        ),
        "example_property_1": Property(
            category="General",
            name="Example Property 1",
            enabled=False,
            args=dict(example_setting=bool),
        ),
        "example_property_2": Property(
            category="General",
            name="Example Property 2",
            enabled=False,
            args=dict(example_setting=bool),
        ),
    }


@dataclass
class Material:
    """Definition of a Material.

    Attributes:
        name: name of this material
        properties: dictionary containing all properties for this Material
    """

    name: str
    properties: Properties_Dict_Type = field(default_factory=PROPERTIES)
