"""Test the AssignConditionsDialog class."""

from meshio import Mesh

from solidity_gui.main.assign_conditions_dialog import AssignConditionsDialog
from solidity_gui.main.condition import (
    Condition,
    ConditionAssignment,
    condition_assignment_datastore,
    condition_datastore,
)
from solidity_gui.main.meshes import mesh_datastore


def test_assign_populate_combos(qtbot):
    """Test the _populate_combos method of the AssignConditionsDialog class."""
    dialog = AssignConditionsDialog()

    condition = Condition(name="foo")
    condition_datastore.add(condition)

    cell_set_name = "cell_set_name"
    mesh = Mesh(points=[], cells={"line": []}, cell_sets={cell_set_name: [[], [], []]})
    mesh_name = "default"
    mesh_datastore[mesh_name] = mesh

    dialog._populate_combos()

    assert dialog.select_component_combo.count() == 1
    assert dialog.select_condition_combo.count() == 1


def test_assign_add_clicked(qtbot):
    """Test the _save_clicked method of the AssignConditionsDialog class."""
    dialog = AssignConditionsDialog()

    cell_set_name = "component"

    condition = Condition(name="foo")
    condition_id = condition_datastore.add(condition)
    dialog.select_component_combo.addItem(cell_set_name)
    dialog.select_condition_combo.addItem("condition_name", userData=condition_id)

    dialog._add_clicked()

    assert condition_assignment_datastore == {
        0: ConditionAssignment(condition=condition, cell_set_name=cell_set_name)
    }


def test_assign_remove_clicked(qtbot):
    """Test the _remove_clicked method of the AssignConditionsDialog class."""
    dialog = AssignConditionsDialog()

    cell_set_name = "component"

    condition = Condition(name="foo")
    condition_id = condition_datastore.add(condition)
    dialog.select_component_combo.addItem(cell_set_name)
    dialog.select_condition_combo.addItem("condition_name", userData=condition_id)

    condition_assignment_datastore == {
        0: ConditionAssignment(condition=condition, cell_set_name=cell_set_name)
    }

    dialog.condition_assignment_table.selectRow(0)
    dialog._remove_clicked()

    assert condition_assignment_datastore == {}
