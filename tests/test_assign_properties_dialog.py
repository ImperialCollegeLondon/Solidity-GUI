"""Test the AssignPropertiesDialog class."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QDialogButtonBox

from solidity_gui.main.assign_properties_dialog import AssignPropertiesDialog
from solidity_gui.main.material import MaterialAssignment, material_assignment_datastore


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


def test_assign_save_clicked(qtbot):
    """Test the _save_clicked method of the AssignPropertiesDialog class."""
    dialog = AssignPropertiesDialog()

    cell_set_name = "component"
    material_id = 0
    dialog.select_component_combo.addItem(cell_set_name)
    dialog.select_material_combo.addItem("material_name", userData=material_id)

    dialog._save_clicked()

    assert material_assignment_datastore == {
        0: MaterialAssignment(material_id=material_id, cell_set_name=cell_set_name)
    }
