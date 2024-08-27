"""Tests for the data preparation logic for mat.txt file generation."""

import pytest

from solidity_gui.main.material import (
    PROPERTIES,
    JointInterfaceMaterial,
    JointMaterialDatastore,
    Material,
    MaterialDatastore,
)
from solidity_gui.main.solidity_file_generator import (
    JointMaterialData,
    SystemValidationError,
    get_mat_data,
)


def _check_joint_material(joint_material_data, index1, index2, properties):
    joint = properties["joint"].default_data
    assert joint_material_data == JointMaterialData(
        index1,
        index2,
        dict(
            tensile_strength=joint["tensile_strength"],
            internal_friction_coefficient=joint["internal_friction_coefficient"],
            cohesion=joint["cohesion"],
            energy_release_rate_mode_1=joint["energy_release_rate_mode_1"],
            energy_release_rate_mode_2=joint["energy_release_rate_mode_2"],
        ),
    )


def test_get_mat_data():
    """Check joint material data with no interfaces."""
    mat1 = Material.from_properties_dict(
        "mat1", dict(joint=PROPERTIES()["joint"].default_data)
    )
    mat2 = Material("mat2")
    materials = MaterialDatastore("materials", {0: mat1, 1: mat2})

    mat_data = get_mat_data([], {}, materials)

    assert mat_data["num_materials"] == 1
    _check_joint_material(mat_data["joint_materials"][0], 1, 1, mat1.properties)


def test_get_mat_data_joint_interface():
    """Check joint material data with an interface between different joint materials."""
    mat1 = Material.from_properties_dict(
        "mat1", dict(joint=PROPERTIES()["joint"].default_data, density=dict(density=2))
    )
    mat2 = Material("mat2")
    mat3 = Material.from_properties_dict(
        "mat1", dict(joint=PROPERTIES()["joint"].default_data, density=dict(density=1))
    )
    materials = MaterialDatastore("materials", {0: mat1, 1: mat2, 2: mat3})

    joint_material_properties = dict(
        tensile_strength=0,
        internal_friction_coefficient=1,
        cohesion=2,
        energy_release_rate_mode_1=3,
        energy_release_rate_mode_2=4,
    )
    joint_materials = JointMaterialDatastore(
        "jm", {0: JointInterfaceMaterial(mat1, mat3, joint_material_properties)}
    )

    mat_data = get_mat_data([(mat1, mat3)], joint_materials, materials)

    assert mat_data["num_materials"] == 3
    _check_joint_material(mat_data["joint_materials"][0], 1, 1, mat1.properties)
    _check_joint_material(mat_data["joint_materials"][1], 3, 3, mat3.properties)
    assert mat_data["joint_materials"][2] == JointMaterialData(
        1, 3, joint_material_properties
    )


def test_get_mat_data_missing_joint_interface_data():
    """Check for validation error if joint material interface parameters not present."""
    mat1 = Material.from_properties_dict(
        "mat1", dict(joint=PROPERTIES()["joint"].default_data, density=dict(density=2))
    )
    mat2 = Material("mat2")
    mat3 = Material.from_properties_dict(
        "mat1", dict(joint=PROPERTIES()["joint"].default_data, density=dict(density=1))
    )
    materials = MaterialDatastore("materials", {0: mat1, 1: mat2, 2: mat3})

    with pytest.raises(SystemValidationError):
        get_mat_data([(mat1, mat3)], JointMaterialDatastore("jm"), materials)
