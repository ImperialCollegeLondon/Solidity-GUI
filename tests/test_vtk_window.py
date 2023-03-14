"""Tests for VTKWindow GUI component."""

from unittest.mock import MagicMock

import pytest
from pubsub import pub

from solidity_gui.main.geometry import Component, generate_mesh
from solidity_gui.main.vtk_window import VTKWindow


@pytest.fixture()
def subscribe_mock(monkeypatch):
    """Magic Mock patched over pubsub.pub.subscribe."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "subscribe", mock)
    return mock


@pytest.fixture()
def send_message_mock(monkeypatch):
    """Magic Mock patched over pubsub.pub.sendMessage."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "sendMessage", mock)
    return mock


@pytest.fixture
def vtk_window(qtbot, subscribe_mock):
    """An AddShapeDialog instance initialised with the shape fixture."""
    window = VTKWindow()
    window.mesh_generator = MagicMock()
    return window


def component_factory(
    shape="ball", label="sphere", kwargs=dict(center=[0.0, 0.0, 0.0], radius=0.2)
):
    """Generate a component with overridable defaults."""
    return Component(shape=shape, label=label, kwargs=kwargs)


def test_vtk_window_init(vtk_window, subscribe_mock):
    """Test VTKWindow is initialised correctly."""
    assert vtk_window.ren
    assert vtk_window.iren
    assert vtk_window.meshes == []

    subscribe_mock.assert_any_call(
        vtk_window._add_component_to_geometry_begin, "geometry.update"
    )
    subscribe_mock.assert_any_call(
        vtk_window._create_mesh_from_geometry_begin, "mesh.create"
    )
    subscribe_mock.assert_any_call(vtk_window._colour_mesh_selection, "mesh.select")


def test_vtk_window_render_mesh(vtk_window):
    """Test render_mesh method of VTKWindow."""
    mesh = generate_mesh([component_factory()], resolution=0.2)

    assert vtk_window.meshes == []
    assert vtk_window.ugrids == []
    vtk_window.render_mesh(mesh)

    # basic checks that mesh has converted to vtk unstructuredgrid properly
    assert vtk_window.ugrids[0].GetNumberOfPoints() == mesh.points.shape[0]
    assert vtk_window.ugrids[0].GetNumberOfCells() == sum(
        block.data.shape[0] for block in mesh.cells
    )


def test_add_component_to_geometry_begin(vtk_window):
    """Test _add_component_to_geometry_begin method of VTKWindow."""
    component = component_factory()
    vtk_window._add_component_to_geometry_begin(component)
    assert vtk_window.components == [component]
    vtk_window.mesh_generator.start_mesh_generation.assert_called_once_with(
        "geometry", [component], resolution=0.2
    )


def test_add_component_to_geometry_end(vtk_window, send_message_mock):
    """Test _add_component_to_geometry_end method of VTKWindow."""
    mesh = MagicMock()
    vtk_window._add_component_to_geometry_end(mesh)
    assert len(vtk_window.meshes) == 1
    assert len(vtk_window.ugrids) == 1
    send_message_mock.assert_called_once_with(
        "geometry.updated", mesh=vtk_window.meshes[0]
    )


def test_create_mesh_from_geometry_begin(vtk_window):
    """Test _create_mesh_from_geometry_begin method of VTKWindow."""
    # create 2 component meshes so we can check we end up with one
    vtk_window._add_component_to_geometry_begin(component_factory())
    vtk_window._add_component_to_geometry_end(MagicMock())
    vtk_window._add_component_to_geometry_begin(component_factory(label="sphere2"))
    vtk_window._add_component_to_geometry_end(MagicMock())
    assert len(vtk_window.meshes) == 2
    vtk_window.mesh_generator.reset_mock()

    vtk_window._create_mesh_from_geometry_begin()
    assert len(vtk_window.ugrids) == 0
    vtk_window.mesh_generator.start_mesh_generation.assert_called_once_with(
        "mesh", vtk_window.components, resolution=0.05
    )


def test_create_mesh_from_geometry_end(vtk_window, send_message_mock):
    """Test _create_mesh_from_geometry_end method of VTKWindow."""
    vtk_window._create_mesh_from_geometry_end(MagicMock())

    assert len(list(vtk_window.ren.GetActors())) == 1
    assert len(vtk_window.meshes) == 1
    assert len(vtk_window.ugrids) == 1
    send_message_mock.assert_called_with("mesh.updated", mesh=vtk_window.meshes[0])
