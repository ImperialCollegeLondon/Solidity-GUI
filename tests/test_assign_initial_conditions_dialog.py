"""Test the AssignConditionsDialog class."""

from meshio import Mesh

from solidity_gui.main.assign_initial_conditions_dialog import (
    AssignInitialConditionsDialog,
)
from solidity_gui.main.initial_condition import (
    InitialCondition,
    InitialConditionAssignment,
    initial_condition_assignment_datastore,
    initial_condition_datastore,
)
from solidity_gui.main.meshes import mesh_datastore


def test_assign_populate_combos(qtbot):
    """Test the _populate_combos method of the AssignInitialConditionsDialog class."""
    dialog = AssignInitialConditionsDialog()

    condition = InitialCondition(name="foo")
    initial_condition_datastore.add(condition)

    cell_set_name = "cell_set_name"
    mesh = Mesh(points=[], cells={"line": []}, cell_sets={cell_set_name: [[], [], []]})
    mesh_name = "default"
    mesh_datastore[mesh_name] = mesh

    dialog._populate_combos()

    assert dialog.select_component_combo.count() == 1
    assert dialog.select_condition_combo.count() == 1


def test_assign_add_clicked(qtbot):
    """Test the _save_clicked method of the AssignInitialConditionsDialog class."""
    dialog = AssignInitialConditionsDialog()

    cell_set_name = "component"

    condition = InitialCondition(name="foo")
    condition_id = initial_condition_datastore.add(condition)
    dialog.select_component_combo.addItem(cell_set_name)
    dialog.select_condition_combo.addItem("condition_name", userData=condition_id)

    dialog._add_clicked()

    assert initial_condition_assignment_datastore == {
        0: InitialConditionAssignment(
            initial_condition=condition, cell_set_name=cell_set_name
        )
    }


def test_assign_remove_clicked(qtbot):
    """Test the _remove_clicked method of the AssignInitialConditionsDialog class."""
    dialog = AssignInitialConditionsDialog()

    cell_set_name = "component"

    condition = InitialCondition(name="foo")
    condition_id = initial_condition_datastore.add(condition)
    dialog.select_component_combo.addItem(cell_set_name)
    dialog.select_condition_combo.addItem("condition_name", userData=condition_id)

    initial_condition_assignment_datastore == {
        0: InitialConditionAssignment(
            initial_condition=condition, cell_set_name=cell_set_name
        )
    }

    dialog.table.selectRow(0)
    dialog._remove_clicked()

    assert initial_condition_assignment_datastore == {}


def test_assign_clear_new_session(qtbot):
    """Test the _clear_assignments method of the AssignInitialConditionsDialog class."""
    from pubsub import pub

    dialog = AssignInitialConditionsDialog()
    dialog.table.insertRow(0)
    assert dialog.table.rowCount() == 1

    pub.sendMessage("session.new")
    assert dialog.table.rowCount() == 0
