"""Tests for VTKWindow GUI component."""
from unittest.mock import MagicMock

import pytest

from solidity_gui.main.components import Component
from solidity_gui.main.geometry import Geometry
from solidity_gui.main.geometry_wrapper import GeometryWrapper
from solidity_gui.main.vtk_window import VTKWindow


@pytest.fixture
def vtk_window(qtbot, subscribe_mock):
    """An AddShapeDialog instance initialised with the shape fixture."""
    window = VTKWindow()
    window.mesh_generator = MagicMock()
    return window


def generate_mesh(components, resolution, label):
    """Helper function to generate meshes from one or more Components."""
    with Geometry() as geom:
        wrapper = GeometryWrapper(geom, label)
        for component in components:
            wrapper.add_component(component, resolution=resolution)

        return wrapper.generate_mesh(resolution)


def component_factory(shape="ball", kwargs=dict(center=[0.0, 0.0, 0.0], radius=0.2)):
    """Generate a component with overridable defaults."""
    return Component(shape=shape, kwargs=kwargs)


def test_vtk_window_init(vtk_window, subscribe_mock):
    """Test VTKWindow is initialised correctly."""
    assert vtk_window.ren
    assert vtk_window.iren

    subscribe_mock.assert_any_call(vtk_window._colour_mesh_selection, "mesh.select")


def test_vtk_window_render_mesh(vtk_window):
    """Test render_mesh method of VTKWindow."""
    mesh_name = "default"
    mesh = generate_mesh([component_factory()], resolution=0.2, label=mesh_name)

    assert vtk_window.ugrids == {}
    vtk_window.render_mesh(mesh_name, mesh)

    # basic checks that mesh has converted to vtk unstructuredgrid properly
    ugrid = vtk_window.ugrids[mesh_name]
    assert ugrid.GetNumberOfPoints() == mesh.points.shape[0]
    assert ugrid.GetNumberOfCells() == mesh.cells_dict["tetra"].shape[0]
