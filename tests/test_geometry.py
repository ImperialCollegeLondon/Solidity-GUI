"""Tests for geometry module."""

from solidity_gui.main.components import Component
from solidity_gui.main.geometry import Geometry
from solidity_gui.main.geometry_wrapper import GeometryWrapper

RESOLUTION = 0.2


def component_factory(shape="ball", kwargs=dict(center=[0.0, 0.0, 0.0], radius=0.2)):
    """Generate a component with overridable defaults."""
    return Component(shape=shape, kwargs=kwargs)


def generate_mesh(components, label, resolution):
    """Helper function to generate meshes from one or more Components."""
    with Geometry() as geom:
        wrapper = GeometryWrapper(geom, label)
        for component in components:
            wrapper.add_component(component)
        return wrapper.generate_mesh([], RESOLUTION)


def check_mesh_cell_sets(mesh, no_points, no_lines, no_surfaces, label):
    """Helper function that checks the cell sets of a mesh are correct."""
    assert len(mesh.cell_sets.keys()) == no_points + no_lines + no_surfaces + 1
    assert mesh.cell_sets_dict[f"{label}_volume_0"]["tetra"] is not None
    for i in range(no_points):
        assert mesh.cell_sets_dict[f"{label}_point_{i}"]["vertex"] is not None
    for i in range(no_lines):
        assert mesh.cell_sets_dict[f"{label}_line_{i}"]["line"] is not None
    for i in range(no_surfaces):
        assert mesh.cell_sets_dict[f"{label}_surface_{i}"]["triangle"] is not None


def test_ball():
    """Test creation of a ball."""
    label = "globe"
    mesh = generate_mesh(
        [Component(shape="ball", kwargs=dict(center=(0, 0, 0), radius=1))],
        label,
        RESOLUTION,
    )
    check_mesh_cell_sets(mesh, 2, 1, 1, label)


def test_box():
    """Test creation of a box."""
    label = "cube"
    mesh = generate_mesh(
        [Component(shape="box", kwargs=dict(x0=(0, 0, 0), extents=(1, 1, 1)))],
        label,
        RESOLUTION,
    )
    check_mesh_cell_sets(mesh, 8, 12, 6, label)


def test_cone():
    """Test creation of a cone."""
    label = "conical"
    mesh = generate_mesh(
        [
            Component(
                shape="cone",
                kwargs=dict(center=(0, 0, 0), axis=(1, 1, 1), radius0=1, radius1=0),
            )
        ],
        label,
        RESOLUTION,
    )
    check_mesh_cell_sets(mesh, 2, 2, 2, label)


def test_cylinder():
    """Test creation of a cylinder."""
    label = "cylindrical"
    mesh = generate_mesh(
        [
            Component(
                shape="cylinder",
                kwargs=dict(x0=(0, 0, 0), axis=(1, 1, 1), radius=1),
            )
        ],
        label,
        RESOLUTION,
    )
    check_mesh_cell_sets(mesh, 2, 3, 3, label)


def test_multiple():
    """Test creating both a box and a ball at the same time."""
    label = "multi"
    mesh = generate_mesh(
        [
            Component(
                shape="box",
                kwargs=dict(x0=(0, 0, 0), extents=(1, 1, 1)),
            ),
            Component(shape="ball", kwargs=dict(center=(0, 0, 0), radius=1)),
        ],
        label,
        RESOLUTION,
    )
    assert len(mesh.cell_sets.keys()) == 32
