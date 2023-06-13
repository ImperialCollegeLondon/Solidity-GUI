"""Tests for the solidity_gui.main.meshes."""
from unittest.mock import MagicMock, patch

from solidity_gui.main.geometry import Component
from solidity_gui.main.gmsh_process import gmsh_process_datastore
from solidity_gui.main.meshes import (
    DEFAULT_RESOLUTION,
    _add_component_to_geometry_begin,
    _add_component_to_geometry_end,
    _create_mesh_from_geometry_begin,
    _create_mesh_from_geometry_end,
    current_mesh,
    mesh_datastore,
)


def component_factory(
    shape="ball", label="sphere", kwargs=dict(center=[0.0, 0.0, 0.0], radius=0.2)
):
    """Generate a component with overridable defaults."""
    return Component(shape=shape, label=label, kwargs=kwargs)


@patch("solidity_gui.main.meshes.GmshProcess")
def test_add_component_to_geometry_begin(gmsh_process_mock):
    """Test _add_component_to_geometry_begin method of VTKWindow."""
    component = component_factory()
    _add_component_to_geometry_begin(component)
    gmsh_process = gmsh_process_datastore[current_mesh]
    assert gmsh_process == gmsh_process_mock()
    gmsh_process.start.assert_called_once_with()
    gmsh_process.call_function_async.assert_called_once_with(
        "add_component", component=component, resolution=DEFAULT_RESOLUTION
    )


def test_add_component_to_geometry_end(send_message_mock):
    """Test _add_component_to_geometry_end method of VTKWindow."""
    mesh = MagicMock()
    assert len(mesh_datastore) == 0
    _add_component_to_geometry_end(mesh)
    assert mesh_datastore[current_mesh] == mesh
    send_message_mock.assert_called_with("geometry.updated", mesh=mesh)


def test_create_mesh_from_geometry_begin():
    """Test _create_mesh_from_geometry_begin method of VTKWindow."""
    assert len(gmsh_process_datastore) == 0
    gmsh_process_mock = MagicMock()
    gmsh_process_datastore[current_mesh] = gmsh_process_mock
    mesh_size = 0.05
    _create_mesh_from_geometry_begin(size=mesh_size)
    gmsh_process_mock.call_function_async.assert_called_once_with(
        "generate_mesh", resolution=mesh_size
    )


def test_create_mesh_from_geometry_end(send_message_mock):
    """Test _create_mesh_from_geometry_end method of VTKWindow."""
    mesh = MagicMock()
    _create_mesh_from_geometry_end(mesh)
    assert mesh_datastore[current_mesh] == mesh
    send_message_mock.assert_called_with("mesh.updated", mesh=mesh)
