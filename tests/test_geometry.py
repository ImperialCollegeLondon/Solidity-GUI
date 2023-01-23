"""Tests for geometry module."""

from unittest.mock import MagicMock, patch

import pytest
from pubsub import pub

from solidity_gui.main.geometry import Component, MeshGenerator, generate_mesh

RESOLUTION = 0.2


@pytest.fixture()
@patch("solidity_gui.main.geometry.Process")
@patch("solidity_gui.main.geometry.GmshListener.start")
def mesh_generator(mock1, mock2):
    """Create a MeshGenerator with Process and QThread monkeypatched."""
    mesh_gen = MeshGenerator()
    mock2.assert_called_once()
    return mesh_gen


@pytest.fixture()
def send_message_mock(monkeypatch):
    """Magic Mock patched over pubsub.pub.sendMessage."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "sendMessage", mock)
    return mock


def component_factory(shape="ball", label="sphere", args=[[0.0, 0.0, 0.0], 0.2]):
    """Generate a component with overridable defaults."""
    return Component(shape=shape, label=label, args=args)


def test_mesh_generator(mesh_generator: MeshGenerator, send_message_mock):
    """Test the basic functionality of MeshGenerator."""
    assert mesh_generator._in_queue.qsize() == 0
    assert mesh_generator._out_queue.qsize() == 0

    mesh_generator.start_mesh_generation("hello", [component_factory()], RESOLUTION)
    send_message_mock.assert_called_once_with("hello.meshing.begin")
    assert mesh_generator._in_queue.qsize() == 1
    assert mesh_generator._out_queue.qsize() == 0

    mesh_generator._generate_mesh()
    assert mesh_generator._in_queue.qsize() == 0
    assert mesh_generator._out_queue.qsize() == 1

    mesh_generator._listener._receive_mesh()
    assert mesh_generator._in_queue.qsize() == 0
    assert mesh_generator._out_queue.qsize() == 0


def test_ball():
    """Test creation of a ball."""
    label = "globe"
    mesh = generate_mesh(
        [Component(shape="ball", args=[(0, 0, 0), 1], label=label)], RESOLUTION
    )
    assert len(mesh.cell_sets.keys()) == 9
    assert mesh.cell_sets[f"{label}_volume"][2] is not None
    for i in range(8):
        assert mesh.cell_sets[f"{label}_surface_{i}"][1] is not None


def test_box():
    """Test creation of a box."""
    label = "cube"
    mesh = generate_mesh(
        [Component(shape="box", args=[0, 1, 0, 1, 0, 1], label=label)], RESOLUTION
    )
    assert len(mesh.cell_sets.keys()) == 7
    assert mesh.cell_sets[f"{label}_volume"][2] is not None
    for i in range(6):
        assert mesh.cell_sets[f"{label}_surface_{i}"][1] is not None


def test_both():
    """Test creating both a box and a ball."""
    box_label = "cube"
    ball_label = "globe"
    mesh = generate_mesh(
        [
            Component(shape="box", args=[0, 1, 0, 1, 0, 1], label=box_label),
            Component(shape="ball", args=[(0, 0, 0), 1], label=ball_label),
        ],
        RESOLUTION,
    )
    assert len(mesh.cell_sets.keys()) == 16
