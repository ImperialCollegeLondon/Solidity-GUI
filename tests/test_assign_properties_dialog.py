"""Test the AssignPropertiesDialog class."""

from meshio import Mesh

from solidity_gui.main.assign_properties_dialog import AssignPropertiesDialog
from solidity_gui.main.material import (
    Material,
    MaterialAssignment,
    material_assignment_datastore,
    material_datastore,
)
from solidity_gui.main.meshes import mesh_datastore


def test_assign_populate_combos(qtbot):
    """Test the _populate_combos method of the AssignPropertiesDialog class."""
    dialog = AssignPropertiesDialog()

    material = Material(name="foo")
    material_datastore.add(material)

    cell_set_name = "cell_set_name"
    mesh = Mesh(points=[], cells={"line": []}, cell_sets={cell_set_name: [[], [], []]})
    mesh_name = "default"
    mesh_datastore[mesh_name] = mesh

    dialog._populate_combos()

    assert dialog.select_component_combo.count() == 1
    assert dialog.select_material_combo.count() == 1


def test_assign_add_clicked(qtbot):
    """Test the _save_clicked method of the AssignPropertiesDialog class."""
    dialog = AssignPropertiesDialog()

    cell_set_name = "component"

    material = Material(name="foo")
    material_id = material_datastore.add(material)
    dialog.select_component_combo.addItem(cell_set_name)
    dialog.select_material_combo.addItem("material_name", userData=material_id)

    dialog._add_clicked()

    assert material_assignment_datastore == {
        0: MaterialAssignment(material=material, cell_set_name=cell_set_name)
    }


def test_assign_remove_clicked(qtbot):
    """Test the _remove_clicked method of the AssignPropertiesDialog class."""
    dialog = AssignPropertiesDialog()

    cell_set_name = "component"

    material = Material(name="foo")
    material_id = material_datastore.add(material)
    dialog.select_component_combo.addItem(cell_set_name)
    dialog.select_material_combo.addItem("material_name", userData=material_id)

    material_assignment_datastore == {
        0: MaterialAssignment(material=material, cell_set_name=cell_set_name)
    }

    dialog.material_assignment_table.selectRow(0)
    dialog._remove_clicked()

    assert material_assignment_datastore == {}
