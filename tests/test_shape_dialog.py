"""Tests for the add_shape_dialogue module."""

from unittest.mock import MagicMock

import pytest
from pubsub import pub
from qtpy import QtCore

from solidity_gui.main.add_shape_dialogue import AddShapeDialog, _get_args
from solidity_gui.main.geometry import Component, Shape


def test_get_args(shape):
    """Test conversion of input data via _get_args helper function."""
    inputs = [1, "aa", 3, 2]
    args = _get_args(inputs, shape.args)
    assert args == [[1.0, "aa"], 3.0, 2]
    assert type(args[0][0]) is float
    assert type(args[0][1]) is str
    assert type(args[1]) is float
    assert type(args[2]) is int


@pytest.fixture
def shape(monkeypatch):
    """Dummy Shape instance that is registered in solidity_gui.main.geometry.SHAPES."""
    shape = Shape(
        name="shape",
        method=MagicMock(),
        args=dict(a=(float, str), b=float, c=int),
    )
    monkeypatch.setattr("solidity_gui.main.geometry.SHAPES", dict(shape=shape))
    return shape


@pytest.fixture
def close_mock(monkeypatch):
    """Magic Mock patched over AddShapeDialog.close."""
    mock = MagicMock()
    monkeypatch.setattr(AddShapeDialog, "close", mock)
    return mock


@pytest.fixture
def dialog(qtbot, shape, close_mock):
    """An AddShapeDialog instance initialised with the shape fixture."""
    dialog = AddShapeDialog(shape)
    qtbot.addWidget(dialog)  # recommended for test clean up
    return dialog


@pytest.fixture()
def send_message_mock(monkeypatch):
    """Magic Mock patched over pubsub.pub.sendMessage."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "sendMessage", mock)
    return mock


def test_dialog_inputs(qtbot, shape):
    """Test dialog has correct number of inputs."""
    dialog = AddShapeDialog(shape)
    qtbot.addWidget(dialog)
    assert len(dialog.inputs) == 4


def test_dialog_ok(close_mock, send_message_mock, dialog, qtbot, shape):
    """Test successful submission of dialog with correct data."""
    values = ["1.0", "etete", "3.0", "4"]
    for val, inp in zip(values, dialog.inputs):
        inp.setText(val)

    label = "labeltext"
    dialog.label_field_input.setText(label)

    button = dialog.button_box.buttons()[0]
    assert button.text() == "OK"
    qtbot.mouseClick(button, QtCore.Qt.LeftButton)
    close_mock.assert_called_once()

    # check that geometry update signal was called with correct data
    send_message_mock.assert_called_once_with(
        "geometry.update",
        component=Component(
            label=label, args=[[1.0, "etete"], 3.0, 4], shape=shape.name
        ),
    )


def test_dialog_cancel(close_mock, dialog, qtbot):
    """Test behaviour of dialog cancel button."""
    button = dialog.button_box.buttons()[1]
    assert button.text() == "Cancel"
    qtbot.mouseClick(button, QtCore.Qt.LeftButton)
    close_mock.assert_called_once()
