"""Tests for the add_shape_dialogue module."""

from unittest.mock import MagicMock

import pytest
from pubsub import pub

from solidity_gui.main.add_shape_dialogue import AddShapeDialog
from solidity_gui.main.forms import Form
from solidity_gui.main.forms.fields import FloatField, IntField, VectorField
from solidity_gui.main.geometry import Component, Shape


class ShapeForm(Form):
    """Form for simple test shape."""

    a = VectorField()
    b = FloatField()
    c = IntField()


@pytest.fixture
def shape(monkeypatch):
    """Dummy Shape instance that is registered in solidity_gui.main.geometry.SHAPES."""
    shape = Shape(name="shape", method=MagicMock(), form=ShapeForm)
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


def test_dialog_form_info(qtbot, shape):
    """Test dialog has correct number of inputs."""
    dialog = AddShapeDialog(shape)
    qtbot.addWidget(dialog)
    form_info = dialog.form_info
    for name, field in ShapeForm.fields.items():
        input_ = form_info.fields[name].input
        if isinstance(input_, list):
            for i in input_:
                assert isinstance(i, field.widget_class.qt_input_class)
        else:
            assert isinstance(input_, field.widget_class.qt_input_class)


def test_dialog_ok(close_mock, send_message_mock, dialog, qtbot, shape):
    """Test successful submission of dialog with correct data."""
    label = "foo"
    data = dict(a=[0, 1, 2], b=3.5, c=1)

    form_fields = dialog.form_info.fields
    for input_, value in zip(form_fields["a"].input, data["a"]):
        input_.setValue(value)
    form_fields["b"].input[0].setValue(data["b"])
    form_fields["c"].input[0].setValue(data["c"])
    form_fields["label"].input[0].setText(label)

    layout = dialog.layout()
    button_box = layout.itemAt(layout.count() - 1).widget()

    button_box.accepted.emit()
    close_mock.assert_called_once()

    # check that geometry update signal was called with correct data
    send_message_mock.assert_called_once_with(
        "geometry.update",
        component=Component(label=label, kwargs=data, shape=shape.name),
    )


def test_dialog_cancel(close_mock, dialog, qtbot):
    """Test behaviour of dialog cancel button."""
    layout = dialog.layout()
    button_box = layout.itemAt(layout.count() - 1).widget()
    button_box.rejected.emit()
    close_mock.assert_called_once()
