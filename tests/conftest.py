"""Pytest configuration file."""
from unittest.mock import MagicMock

import pytest
from pubsub import pub


@pytest.fixture()
def subscribe_mock(monkeypatch):
    """Magic Mock patched over pubsub.pub.subscribe."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "subscribe", mock)
    return mock
