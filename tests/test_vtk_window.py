"""Tests for VTKWindow GUI component."""
from unittest.mock import MagicMock

import pytest

from solidity_gui.main.geometry import Component, Geometry, ShapeFactory
from solidity_gui.main.vtk_window import VTKWindow


@pytest.fixture
def vtk_window(qtbot, subscribe_mock):
    """An AddShapeDialog instance initialised with the shape fixture."""
    window = VTKWindow()
    window.mesh_generator = MagicMock()
    return window


def generate_mesh(components, resolution):
    """Helper function to generate meshes from one or more Components."""
    with Geometry() as geom:
        factory = ShapeFactory(geom)
        for component in components:
            factory.add_component(component, resolution=resolution)

        return geom.generate_mesh()


def component_factory(
    shape="ball", label="sphere", kwargs=dict(center=[0.0, 0.0, 0.0], radius=0.2)
):
    """Generate a component with overridable defaults."""
    return Component(shape=shape, label=label, kwargs=kwargs)


def test_vtk_window_init(vtk_window, subscribe_mock):
    """Test VTKWindow is initialised correctly."""
    assert vtk_window.ren
    assert vtk_window.iren

    subscribe_mock.assert_any_call(vtk_window._colour_mesh_selection, "mesh.select")


def test_vtk_window_render_mesh(vtk_window):
    """Test render_mesh method of VTKWindow."""
    mesh = generate_mesh([component_factory()], resolution=0.2)

    assert vtk_window.ugrid is None
    vtk_window.render_mesh(mesh)

    # basic checks that mesh has converted to vtk unstructuredgrid properly
    assert vtk_window.ugrid.GetNumberOfPoints() == mesh.points.shape[0]
    assert vtk_window.ugrid.GetNumberOfCells() == sum(
        block.data.shape[0] for block in mesh.cells
    )
