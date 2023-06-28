"""Module containing definitions for bundling material and properties data."""

from dataclasses import dataclass, field
from typing import Dict, Optional, Type

from meshio import Mesh
from pubsub import pub

from .datastore import IndexDatastore
from .forms import Form
from .forms.fields import FloatField
from .meshes import mesh_datastore

Attributes_Dict_Type = Dict[str, Type[float] | bool]


class DensityForm(Form):
    """Form for collecting material density data."""

    density = FloatField()


class ElasticityForm(Form):
    """Form for collecting material properties related to elasticity."""

    lames_first_parameter = FloatField(display_name="Lamé's First Parameter")
    lames_second_parameter = FloatField(display_name="Lamé's Second Parameter")


class FractureForm(Form):
    """Form for collecting properties related to fracturing."""

    damage_delta_0 = FloatField(display_name="Damage Delta 0")
    damage_delta_1 = FloatField(display_name="Damage Delta 1")
    damage_threshold = FloatField(display_name="Damage Threshold")


class OtherForm(Form):
    """Temporary form for all remaining material properties."""

    mass_damping_coefficient = FloatField(display_name="Mass Damping Coefficient")
    penalty_number = FloatField(display_name="Penalty Number")
    energy_release_rate_mode_1 = FloatField(display_name="Energy Release Rate - Mode 1")
    energy_release_rate_mode_2 = FloatField(display_name="Energy Release Rate - Mode 2")
    tensile_strength = FloatField(display_name="Tensile Strength")
    cohesion = FloatField(display_name="Cohesion")
    internal_friction_coefficient = FloatField(
        display_name="Internal Friction Coefficient"
    )
    sliding_friction_coefficient = FloatField(
        display_name="Sliding Friction Coefficient"
    )
    static_friction_coefficient = FloatField(display_name="Static Friction Coefficient")
    pressure_friction_coefficient = FloatField(
        display_name="Pressure Friction Coefficient"
    )
    velocity_factor = FloatField(display_name="Velocity Factor")
    pressure_factor = FloatField(display_name="Pressure Factor")
    mass_ratio_coefficent = FloatField(display_name="Mass Ratio Coefficient")


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
    attributes: Type[Form]
    data: Optional[Dict[str, object]] = None
    default_data: Dict[str, object] = field(default_factory=dict)


Properties_Dict_Type = dict[str, Property]


def PROPERTIES() -> Properties_Dict_Type:
    """Define the dictionary of available properties for a Material."""
    return {
        "density": Property(
            category="General",
            name="Density",
            enabled=False,
            attributes=DensityForm,
            default_data=dict(density=2.34e10),
        ),
        "elasticity": Property(
            category="Mechanical",
            name="Elasticity",
            enabled=False,
            attributes=ElasticityForm,
            default_data=dict(
                lames_first_parameter=2.23325062035e10,
                lames_second_parameter=2.41935483871e10,
            ),
        ),
        "fracture": Property(
            category="Mechanical",
            name="Fracture",
            enabled=False,
            attributes=FractureForm,
            default_data=dict(
                damage_delta_0=0.005,
                damage_delta_1=1,
                damage_threshold=0.5,
            ),
        ),
        "other": Property(
            category="Other",
            name="Other",
            enabled=False,
            attributes=OtherForm,
            default_data=dict(
                mass_damping_coefficient=0.0,
                penalty_number=2e10,
                energy_release_rate_mode_1=50.0,
                energy_release_rate_mode_2=50.0,
                tensile_strength=1e7,
                cohesion=3.5e7,
                internal_friction_coefficient=0.577,
                sliding_friction_coefficient=0.6,
                static_friction_coefficient=0.0,
                pressure_friction_coefficient=0.0,
                velocity_factor=0.0,
                pressure_factor=1.0,
                mass_ratio_coefficent=0.1,
            ),
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


@dataclass(frozen=True)
class MaterialAssignment:
    """Simple datastructure recording the association of a cell_set and Material."""

    material: Material
    cell_set_name: str


class MaterialDatastore(IndexDatastore[Material]):
    """Convenience IndexDatastore subclass with concretised type."""


material_datastore = MaterialDatastore("materials")
material_assignment_datastore: IndexDatastore[MaterialAssignment] = IndexDatastore(
    "material_assignment"
)


def sync_assignments_material_removed(key: int, value: Material) -> None:
    """Message handler sync assignment datastore when material datastore changes."""
    for assignment_key, assignment in list(material_assignment_datastore.items()):
        if assignment.material == value:
            del material_assignment_datastore[assignment_key]


def sync_assignments_mesh_removed(key: int, value: Mesh) -> None:
    """Message handler sync assignment datastore when mesh datastore changes."""
    for assignment_key, assignment in list(material_assignment_datastore.items()):
        for cell_set_name in value.cell_sets:
            if assignment.cell_set_name == cell_set_name:
                del material_assignment_datastore[assignment_key]
                break


pub.subscribe(sync_assignments_material_removed, material_datastore.remove_topic)
pub.subscribe(sync_assignments_mesh_removed, mesh_datastore.remove_topic)
