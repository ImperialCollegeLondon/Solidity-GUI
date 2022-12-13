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


@pytest.fixture
def vtk_window(qtbot, subscribe_mock):
    """An AddShapeDialog instance initialised with the shape fixture."""
    window = VTKWindow()
    return window


def test_vtk_window_init(vtk_window, subscribe_mock):
    """Test VTKWindow is initialised correctly."""
    assert vtk_window.ren
    assert vtk_window.iren
    assert vtk_window.actor
    assert vtk_window.mesh is None
    subscribe_mock.assert_called_once_with(vtk_window._update_mesh, "mesh.update")


def test_vtk_window_render_mesh(vtk_window):
    """Test render_mesh method of VTKWindow."""
    mesh = generate_mesh(
        [Component(shape="ball", args=[[0.0, 0.0, 0.0], 1.0], label="sphere")]
    )
    vtk_window.render_mesh(mesh)

    assert vtk_window.mapper
    assert vtk_window.lut

    # basic checks that mesh has converted to vtk unstructuredgrid properly
    assert vtk_window.ugrid.GetNumberOfPoints() == mesh.points.shape[0]
    assert vtk_window.ugrid.GetNumberOfCells() == sum(
        block.data.shape[0] for block in mesh.cells
    )
