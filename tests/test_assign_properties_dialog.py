"""Test the AssignPropertiesDialog class."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from meshio import Mesh
from PySide6.QtWidgets import QDialogButtonBox

from solidity_gui.main.assign_properties_dialog import AssignPropertiesDialog


@pytest.fixture
def handler_mocks(monkeypatch):
    """Fixture that mocks the signal handlers of the AssignPropertiesDialog class."""
    save_mock = MagicMock()
    monkeypatch.setattr(AssignPropertiesDialog, "_save_clicked", save_mock)
    close_mock = MagicMock()
    monkeypatch.setattr(AssignPropertiesDialog, "close", close_mock)
    return SimpleNamespace(save=save_mock, close=close_mock)


def test_assign_properties(qtbot, handler_mocks, subscribe_mock):
    """Test AssignPropertiesDialog class."""
    dialog = AssignPropertiesDialog()
    dialog_layout = dialog.layout()
    button_box = dialog_layout.itemAt(dialog_layout.count() - 1).widget()
    assert isinstance(button_box, QDialogButtonBox)

    # simplest way to check that signal handlers seems to be to replace handlers with a
    # mock then trigger the signal and check the calls
    handler_mocks.save.assert_not_called()
    button_box.accepted.emit()
    handler_mocks.save.assert_called()

    handler_mocks.close.assert_not_called()
    button_box.rejected.emit()
    handler_mocks.close.assert_called()

    subscribe_mock.assert_any_call(dialog._set_components, "geometry.updated")
    subscribe_mock.assert_any_call(dialog._set_materials, "materials.add")


def test_assign_set_components():
    """Test the _set_components method of the AssignPropertiesDialog class."""
    dialog = AssignPropertiesDialog()

    assert dialog.select_component_combo.count() == 0

    mesh = Mesh(cell_sets={"test": None}, points=[], cells={})
    dialog._set_components(mesh)

    assert dialog.select_component_combo.count() == 1


def test_assign_set_materials():
    """Test the _set_materials method of the AssignPropertiesDialog class."""
    dialog = AssignPropertiesDialog()

    assert dialog.select_material_combo.count() == 0

    dialog._set_materials("test")

    assert dialog.select_material_combo.count() == 1


def test_assign_save_clicked():
    """Test the _save_clicked method of the AssignPropertiesDialog class."""
    dialog = AssignPropertiesDialog()

    dialog.select_component_combo.addItem("test")
    dialog.select_material_combo.addItem("test")

    dialog._save_clicked()

    assert dialog.assigned_materials == {"test": "test"}
