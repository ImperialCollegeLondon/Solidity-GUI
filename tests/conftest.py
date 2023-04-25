"""Test configuration and fixtures."""
from unittest.mock import MagicMock

import pytest
from pubsub import pub
from pytest import MonkeyPatch

from solidity_gui.main.geometry import component_datastore
from solidity_gui.main.material import material_assignment_datastore, material_datastore
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
    mesh_datastore.clear()
    component_datastore.clear()
    material_datastore.clear()
    material_assignment_datastore.clear()
