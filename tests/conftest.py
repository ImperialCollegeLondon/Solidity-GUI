"""Test configuration and fixtures."""
from unittest.mock import MagicMock

import pytest
from pubsub import pub


@pytest.fixture()
def send_message_mock(monkeypatch):
    """Magic Mock patched over pubsub.pub.sendMessage."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "sendMessage", mock)
    return mock
