"""Test the InitialConditionsManagerDialog class."""

from solidity_gui.main.initial_conditions_manager_dialog import (
    InitialConditionsManagerDialog,
)


def test_manager_clear_new_session(qtbot):
    """Test the _clear_conditions method of the InitialConditionsManagerDialog class."""
    from pubsub import pub

    dialog = InitialConditionsManagerDialog()
    dialog.table.insertRow(0)
    assert dialog.table.rowCount() == 1

    pub.sendMessage("session.new")
    assert dialog.table.rowCount() == 0
