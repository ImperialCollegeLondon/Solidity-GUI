"""Module containing definitions for bundling material and properties data."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TypeGuard

from marshmallow import validate
from meshio import Mesh
from pubsub import pub

from .assignment_base import AssignmentBase
from .datastore import Datastore, IndexDatastore
from .forms import Form
from .forms.fields import FloatField, WiderFloatField
from .gmsh_process import GmshProcess
from .meshes import mesh_datastore

Attributes_Dict_Type = dict[str, type[float] | bool]


class DensityForm(Form):
    """Form for collecting material density data."""

    density = FloatField()


class ElasticityForm(Form):
    """Form for collecting material properties related to elasticity."""

    youngs_modulus = FloatField(
        display_name="Young's Modulus",
        validators=[validate.Range(min=0, max=1e11)],
    )
    poissons_ratio = FloatField(
        display_name="Poisson's Ratio",
        validators=[
            validate.Range(min=-1.0, max=0.5, min_inclusive=False, max_inclusive=False)
        ],
    )


class DamageForm(Form):
    """Form for collecting properties related to fracturing."""

    damage_delta_0 = WiderFloatField(display_name="Damage Delta 0")
    damage_delta_1 = FloatField(display_name="Damage Delta 1")
    damage_threshold = FloatField(display_name="Damage Threshold")


class OtherForm(Form):
    """Temporary form for all remaining material properties."""

    mass_damping_coefficient = FloatField(display_name="Mass Damping Coefficient")
    penalty_number = FloatField(display_name="Penalty Number")
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


class JointForm(Form):
    """Blank form relating to joint elements."""

    energy_release_rate_mode_1 = FloatField(display_name="Energy Release Rate - Mode 1")
    energy_release_rate_mode_2 = FloatField(display_name="Energy Release Rate - Mode 2")
    tensile_strength = FloatField(display_name="Tensile Strength")
    cohesion = FloatField(display_name="Cohesion")
    internal_friction_coefficient = FloatField(
        display_name="Internal Friction Coefficient"
    )
    spring_stiffness = FloatField(display_name="Spring Stiffness")


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
    attributes: type[Form]
    data: dict[str, object] | None = None
    default_data: dict[str, object] = field(default_factory=dict)


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
                poissons_ratio=0.3,
                youngs_modulus=5.9,
                lame_mu=5.9 / (2 * (1 + 0.3)),
                lame_lambda=5.9 * 0.3 / ((1 + 0.3) * (1 - 2 * 0.3)),
            ),
        ),
        "damage": Property(
            category="Mechanical",
            name="Damage",
            enabled=False,
            attributes=DamageForm,
            default_data=dict(
                damage_delta_0=1.0,
                damage_delta_1=1.0,
                damage_threshold=0.0,
            ),
        ),
        "other": Property(
            category="General",
            name="Other",
            enabled=False,
            attributes=OtherForm,
            default_data=dict(
                mass_damping_coefficient=0.0,
                penalty_number=2e10,
                sliding_friction_coefficient=0.6,
                static_friction_coefficient=0.0,
                pressure_friction_coefficient=0.0,
                velocity_factor=0.0,
                pressure_factor=1.0,
                mass_ratio_coefficent=0.1,
            ),
        ),
        "joint": Property(
            category="Joint",
            name="Joint",
            enabled=False,
            attributes=JointForm,
            default_data=dict(
                energy_release_rate_mode_1=50.0,
                energy_release_rate_mode_2=50.0,
                tensile_strength=1e7,
                cohesion=3.5e7,
                internal_friction_coefficient=0.577,
                spring_stiffness=12,
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

    @classmethod
    def from_properties_dict(
        cls, name: str, properties_data: dict[str, dict[str, object]]
    ) -> "Material":
        """Construct a Material instance from a dictionary of property data."""
        material = cls(name=name)
        for property_name, property_data in properties_data.items():
            property_ = material.properties[property_name]
            property_.enabled = True
            property_.data = property_data.copy()
        return material


@dataclass
class MaterialAssignment(AssignmentBase):
    """Simple datastructure recording the association of a cell_set and Material."""

    material: Material


class MaterialDatastore(IndexDatastore[Material]):
    """Convenience IndexDatastore subclass with concretised type."""

    def get_by_name(self, name: str) -> tuple[int, Material]:
        """Retrieve a material using its name.

        Args:
          name: name of the material to get.
        """
        for key, material in self.items():
            if material.name == name:
                return key, material
        raise ValueError(f"Unable to find material with name - {name}")


class MaterialAssignmentDatastore(IndexDatastore[MaterialAssignment]):
    """IndexDatastore subclass with types concretised for MaterialAssignment."""

    def get_by_cell_set_name(self, name: str) -> tuple[int, MaterialAssignment]:
        """Retrieve a material assignment using its cell_set_name.

        Args:
          name: name of the material to get.
        """
        for key, assignment in self.items():
            if assignment.cell_set_name == name:
                return key, assignment
        raise ValueError(
            f"Unable to find material assignment with cell_set_name - {name}"
        )


@dataclass
class JointInterfaceMaterial:
    """Definition of an interface between materials containing joint elements."""

    material1: Material
    material2: Material
    properties: dict[str, object]


class JointMaterialDatastore(IndexDatastore[JointInterfaceMaterial]):
    """IndexDatastore subclass with types concretised for JointInterfaceMaterial."""

    def get_by_materials(
        self, material1: Material, material2: Material
    ) -> JointInterfaceMaterial:
        """Retrieve a joint interface materials using its consituent materials.

        Args:
          material1: first material of the interface
          material2: second material of the interface
        """
        for key, joint_material in self.items():
            if (
                material1 == joint_material.material1
                and material2 == joint_material.material2
            ) or (
                material2 == joint_material.material1
                and material1 == joint_material.material2
            ):
                return joint_material
        raise ValueError(
            "Unable to find JointInterfaceMaterial with materials: "
            f"{material1.name} and {material2.name}"
        )


material_datastore = MaterialDatastore("materials")
material_assignment_datastore = MaterialAssignmentDatastore("material_assignment")
joint_material_datastore = JointMaterialDatastore("joint_material")


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


def sync_joint_material_removed(key: int, value: Material) -> None:
    """Message handler to sync joint material datastore when material removed."""
    for joint_key, joint_material in joint_material_datastore.items():
        if joint_material.material1 == value or joint_material.material2 == value:
            del joint_material_datastore[joint_key]


pub.subscribe(sync_assignments_material_removed, material_datastore.remove_topic)
pub.subscribe(sync_assignments_mesh_removed, mesh_datastore.remove_topic)


def get_joint_material_interfaces(
    gmsh_processes: Datastore[str, GmshProcess],
    material_assignments: MaterialAssignmentDatastore,
) -> list[tuple[Material, Material]]:
    """Find all interfaces between different materials that have joint elements.

    Args:
      gmsh_processes: all gmsh processes containing relevant geometric data
      material_assignments: material assignment information
    """
    joined_materials = []

    for gmsh_process in gmsh_processes.values():
        joined_volume_names = gmsh_process.call_function("get_joined_volumes")

        if not is_iterable_of_2uple_of_string(joined_volume_names):
            raise ValueError("Expected Iterable[tuple[str, str]]")
        for volume_name1, volume_name2 in joined_volume_names:
            try:
                _, assignment1 = material_assignments.get_by_cell_set_name(volume_name1)
                _, assignment2 = material_assignments.get_by_cell_set_name(volume_name2)
            except ValueError:
                continue
            if (
                not assignment1.material.properties["joint"].enabled
                or not assignment2.material.properties["joint"].enabled
            ):
                continue
            joined_material = (assignment1.material, assignment2.material)

            if (
                joined_material not in joined_materials
                and joined_material[::-1] not in joined_materials
            ):
                joined_materials.append(joined_material)
    return joined_materials


def is_iterable_of_2uple_of_string(
    iterable: object,
) -> TypeGuard[Iterable[tuple[str, str]]]:
    """Type guard checking  return type from a get_jointed_volumes function call."""
    if not isinstance(iterable, Iterable):
        return False
    for data in iterable:
        if not isinstance(data, tuple):
            return False
        for val in data:
            if not isinstance(val, str):
                return False
    return True


def calculate_lame_constants(
    youngs_modulus: float, poissons_ratio: float
) -> tuple[float, float]:
    """Calculate Lame's Constants from Young's Modulus and Poisson's Ratio."""
    E = youngs_modulus
    nu = poissons_ratio
    lame_lambda = E * nu / ((1 + nu) * (1 - 2 * nu))
    lame_mu = E / (2 * (1 + nu))
    return lame_lambda, lame_mu
