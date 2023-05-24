"""Tests for the MainWindow class."""
from unittest.mock import patch

from solidity_gui.main.main_window import MainWindow


@patch("solidity_gui.main.vtk_window.MeshGenerator")
def test_close(generator_mock, send_message_mock, monkeypatch, qtbot):
    """Test that closing the main window leads to a pubsub message being sent."""
    window = MainWindow()
    send_message_mock.assert_not_called()

    window.close()
    send_message_mock.assert_called_once_with("window.close")
