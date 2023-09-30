"""Test configuration and fixtures."""
from unittest.mock import MagicMock, patch

import pytest
from pubsub import pub
from pytest import MonkeyPatch

from solidity_gui.main.condition import (
    condition_assignment_datastore,
    condition_datastore,
)
from solidity_gui.main.geometry import Geometry
from solidity_gui.main.geometry_wrapper import GeometryWrapper
from solidity_gui.main.gmsh_process import gmsh_process_datastore
from solidity_gui.main.initial_condition import (
    initial_condition_assignment_datastore,
    initial_condition_datastore,
)
from solidity_gui.main.material import material_assignment_datastore, material_datastore
from solidity_gui.main.mesh_sizes import mesh_size_datastore
from solidity_gui.main.meshes import mesh_datastore


@pytest.fixture()
def subscribe_mock(monkeypatch: MonkeyPatch) -> MagicMock:
    """Magic Mock patched over pubsub.pub.subscribe."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "subscribe", mock)
    return mock


@pytest.fixture()
def send_message_mock(monkeypatch: MonkeyPatch) -> MagicMock:
    """Magic Mock patched over pubsub.pub.sendMessage."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "sendMessage", mock)
    return mock


@pytest.fixture(autouse=True)
def clear_datastores():
    """Clear all datastores before each test."""
    # patch out sendMessage here as the syncing signals can cause issues sometimes
    with patch.object(pub, "sendMessage"):
        mesh_datastore.clear()
        gmsh_process_datastore.clear()
        material_datastore.clear()
        material_assignment_datastore.clear()
        condition_datastore.clear()
        condition_assignment_datastore.clear()
        initial_condition_datastore.clear()
        initial_condition_assignment_datastore.clear()
        mesh_size_datastore.clear()


@pytest.fixture(autouse=True)
def mock_gmsh_process_start(monkeypatch):
    """Prevent any extra threads or processes from being started."""
    monkeypatch.setattr("solidity_gui.main.gmsh_process.GmshProcess.start", MagicMock())


@pytest.fixture
def gw():
    """Convenience fixture for creating an initialised GeometryWrapper instance."""
    with Geometry() as geom:
        yield GeometryWrapper(geom, "geometry_wrapper")
