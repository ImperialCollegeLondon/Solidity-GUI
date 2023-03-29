"""Pytest configuration file."""
from unittest.mock import MagicMock

import pytest
from pubsub import pub
from pytest import MonkeyPatch


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
