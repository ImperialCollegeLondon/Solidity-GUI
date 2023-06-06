"""Tests for the solidity_gui.main.meshes."""
from unittest.mock import MagicMock, patch

from solidity_gui.main.geometry import Component, mesh_generator_datastore
from solidity_gui.main.meshes import (
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


@patch("solidity_gui.main.geometry.MeshGenerator.add_component")
def test_add_component_to_geometry_begin(_):
    """Test _add_component_to_geometry_begin method of VTKWindow."""
    component = component_factory()
    _add_component_to_geometry_begin(component)
    mesh_generator = mesh_generator_datastore[current_mesh]
    mesh_generator.add_component.assert_called_once_with(component)


def test_add_component_to_geometry_end(send_message_mock):
    """Test _add_component_to_geometry_end method of VTKWindow."""
    mesh = MagicMock()
    assert len(mesh_datastore) == 0
    _add_component_to_geometry_end(mesh)
    assert mesh_datastore[current_mesh] == mesh
    send_message_mock.assert_called_with("geometry.updated", mesh=mesh)


def test_create_mesh_from_geometry_begin():
    """Test _create_mesh_from_geometry_begin method of VTKWindow."""
    assert len(mesh_generator_datastore) == 0
    mesh_generator_mock = MagicMock()
    mesh_generator_datastore[current_mesh] = mesh_generator_mock
    mesh_size = 0.05
    _create_mesh_from_geometry_begin(size=mesh_size)
    mesh_generator_mock.start_mesh_generation.assert_called_once_with(
        "mesh", resolution=mesh_size
    )


def test_create_mesh_from_geometry_end(send_message_mock):
    """Test _create_mesh_from_geometry_end method of VTKWindow."""
    mesh = MagicMock()
    _create_mesh_from_geometry_end(mesh)
    assert mesh_datastore[current_mesh] == mesh
    send_message_mock.assert_called_with("mesh.updated", mesh=mesh)
