"""Test the AssignPropertiesDialog class."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
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
    subscribe_mock.assert_any_call(dialog._add_material, "materials.add")
    subscribe_mock.assert_any_call(dialog._remove_material, "materials.remove")


def test_assign_add_material(qtbot):
    """Test the _add_material method of the AssignPropertiesDialog class."""
    dialog = AssignPropertiesDialog()

    assert dialog.select_material_combo.count() == 0

    dialog._add_material("test")

    assert dialog.select_material_combo.count() == 1


def test_assign_remove_material(qtbot):
    """Test the _remove_material method of the AssignPropertiesDialog class."""
    dialog = AssignPropertiesDialog()

    dialog.select_material_combo.addItem("test")
    dialog.assigned_materials["test"] = "test"

    assert dialog.select_material_combo.count() == 1
    assert dialog.assigned_materials == {"test": "test"}

    dialog._remove_material("test")

    assert dialog.select_material_combo.count() == 0
    assert dialog.assigned_materials == {}


def test_assign_save_clicked(qtbot):
    """Test the _save_clicked method of the AssignPropertiesDialog class."""
    dialog = AssignPropertiesDialog()

    dialog.select_component_combo.addItem("test")
    dialog.select_material_combo.addItem("test")

    dialog._save_clicked()

    assert dialog.assigned_materials == {"test": "test"}
