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

    lames_first_parameter = FloatField(display_name="Lame's First Parameter")
    lames_second_parameter = FloatField(display_name="Lame's Second Parameter")


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

    material_id: int
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
        if assignment.material_id == key:
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
