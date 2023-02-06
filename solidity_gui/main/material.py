from dataclasses import dataclass, field
from typing import Dict, Tuple, Type

Arg_Dict_Type = Dict[str, Tuple[Type[float], Type[float], Type[float]] | Type[float]]

@dataclass
class Property:
    category: str
    name: str
    enabled: bool
    args: Arg_Dict_Type

Properties_Dict_Type = dict[str, Property]
def PROPERTIES():
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
    name: str
    properties: Properties_Dict_Type = field(default_factory=PROPERTIES)