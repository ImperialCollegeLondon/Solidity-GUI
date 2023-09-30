"""Tests for GeometryWrapper class."""
import gmsh
import numpy as np
import pytest

from solidity_gui.main.mesh_sizes import MeshSize
from solidity_gui.main.meshes import get_cell_offset


@pytest.fixture
def gw(gw):
    """Extend gw fixture to do common test setup."""
    gw.geom.add_ball((0, 0, 0), 1)
    gw.geom.synchronize()
    gw.generate_mesh([], None)  # get rough mesh so that cell_set_to_entity is defined
    yield gw


def test_generate_mesh(gw):
    """Basic test for generate_mesh method."""
    mesh = gw.generate_mesh([], None)
    for name in (
        f"{gw.label}_volume_0",
        f"{gw.label}_surface_0",
        f"{gw.label}_line_0",
        f"{gw.label}_point_0",
        f"{gw.label}_point_1",
    ):
        assert name in mesh.cell_sets

    # volume_0 cell_set should contain all tetra
    cell_set = mesh.cell_sets_dict[f"{gw.label}_volume_0"]
    assert set(cell_set.keys()) == {"tetra"}
    assert np.all(
        np.arange(mesh.cells_dict["tetra"].shape[0])
        == np.sort(cell_set["tetra"]) - get_cell_offset(mesh.cells_dict, "tetra")
    )

    # surface_0 cell set should contain all triangles
    cell_set = mesh.cell_sets_dict[f"{gw.label}_surface_0"]
    assert set(cell_set.keys()) == {"triangle"}
    assert np.all(
        np.arange(mesh.cells_dict["triangle"].shape[0])
        == np.sort(cell_set["triangle"]) - get_cell_offset(mesh.cells_dict, "triangle")
    )
    assert np.all(np.array([0, 0]) == gmsh.model.mesh.get_sizes([(3, 1)]))


def test_generate_mesh_default_size(gw):
    """Test assignment of mesh sizes using default value."""
    mesh_size = 0.1
    gw.generate_mesh([], mesh_size)
    point_0_size, point_1_size = gmsh.model.mesh.get_sizes([(0, 1), (0, 2)])
    assert point_0_size == mesh_size
    assert point_1_size == mesh_size


def test_generate_mesh_one_point_mesh_size(gw):
    """Test assignment of mesh sizes for a single point."""
    cell_set_name = f"{gw.label}_point_0"
    mesh_size = 0.1
    default_mesh_size = 0.2
    gw.generate_mesh(
        [MeshSize(cell_set_name=cell_set_name, size=mesh_size)], default_mesh_size
    )

    point_0_size, point_1_size = gmsh.model.mesh.get_sizes([(0, 1), (0, 2)])
    assert point_0_size == mesh_size
    assert point_1_size == default_mesh_size


def test_generate_mesh_two_point_mesh_size(gw):
    """Test assignment of mesh sizes for two separate points."""
    mesh_size_0 = 0.1
    mesh_size_1 = 0.2
    gw.generate_mesh(
        [
            MeshSize(cell_set_name=f"{gw.label}_point_0", size=mesh_size_0),
            MeshSize(cell_set_name=f"{gw.label}_point_1", size=mesh_size_1),
        ],
        None,
    )

    point_0_size, point_1_size = gmsh.model.mesh.get_sizes([(0, 1), (0, 2)])
    assert point_0_size == mesh_size_0
    assert point_1_size == mesh_size_1


@pytest.mark.parametrize("entity", ("volume", "surface", "line"))
def test_generate_mesh_higher_dim_mesh_size(entity, gw):
    """Test assignment of mesh sizes to lines, surfaces and volumes."""
    mesh_size = 0.1
    gw.generate_mesh(
        [MeshSize(cell_set_name=f"{gw.label}_{entity}_0", size=mesh_size)], 0.3
    )

    point_0_size, point_1_size = gmsh.model.mesh.get_sizes([(0, 1), (0, 2)])
    assert point_0_size == mesh_size
    assert point_1_size == mesh_size


@pytest.mark.parametrize("entity", ("volume", "surface", "line"))
def test_generate_mesh_size_dimension_precendence(entity, gw):
    """Test that mesh sizes for lower dimension entities take precendence."""
    mesh_size_0, mesh_size_1 = 0.1, 0.2
    gw.generate_mesh(
        [
            MeshSize(cell_set_name=f"{gw.label}_{entity}_0", size=mesh_size_1),
            MeshSize(cell_set_name=f"{gw.label}_point_0", size=mesh_size_0),
        ],
        0.3,
    )

    point_0_size, point_1_size = gmsh.model.mesh.get_sizes([(0, 1), (0, 2)])
    assert point_0_size == mesh_size_0
    assert point_1_size == mesh_size_1

    # check we get the same if sizes are given in a different order
    gw.generate_mesh(
        [
            MeshSize(cell_set_name=f"{gw.label}_point_0", size=mesh_size_0),
            MeshSize(cell_set_name=f"{gw.label}_{entity}_0", size=mesh_size_1),
        ],
        0.3,
    )

    point_0_size, point_1_size = gmsh.model.mesh.get_sizes([(0, 1), (0, 2)])
    assert point_0_size == mesh_size_0
    assert point_1_size == mesh_size_1
