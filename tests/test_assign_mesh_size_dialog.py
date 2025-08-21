"""Test the AssignMeshSizeDialog class."""

import pytest
from meshio import Mesh

from solidity_gui.main.assign_mesh_size_dialog import AssignMeshSizeDialog
from solidity_gui.main.mesh_sizes import MeshSize, mesh_size_datastore
from solidity_gui.main.meshes import mesh_datastore


@pytest.mark.parametrize(
    "cell_sets",
    (("volume",), ("surface",), ("line",), ("point",), (), ("volume", "surface")),
)
def test_assign_populate_combo(cell_sets, qtbot):
    """Test the _populate_combo method of AssignMeshSizeDialog."""
    dialog = AssignMeshSizeDialog()

    mesh = Mesh(
        points=[],
        cells={"line": []},
        cell_sets={name: [[], [], []] for name in cell_sets},
    )
    mesh_name = "default"
    mesh_datastore[mesh_name] = mesh

    dialog._populate_combo()

    assert dialog.component_combo.count() == len(cell_sets)


def test_assign_add_clicked(qtbot):
    """Test the _add_clicked method of AssignMeshSizeDialog."""
    dialog = AssignMeshSizeDialog()

    cell_set_name = "component"
    dialog.component_combo.addItem(cell_set_name)

    mesh_size = 0.1
    dialog.mesh_size_spinbox.setValue(mesh_size)

    dialog._add_clicked()

    assert mesh_size_datastore == {
        0: MeshSize(cell_set_name=cell_set_name, size=mesh_size)
    }


def test_assign_remove_clicked(qtbot):
    """Test the _remove_clicked method of AssignMeshSizeDialog."""
    dialog = AssignMeshSizeDialog()

    cell_set_name = "component"
    mesh_size = 0.1
    mesh_size = MeshSize(cell_set_name=cell_set_name, size=mesh_size)
    mesh_size_datastore.add(mesh_size)

    dialog.table.add_items([mesh_size])
    dialog.table.selectRow(0)
    dialog._remove_clicked()

    assert mesh_size_datastore == {}


def test_assign_clear_new_session(qtbot):
    """Test the _clear_assignments method of the AssignMeshSizeDialog class."""
    from pubsub import pub

    dialog = AssignMeshSizeDialog()
    dialog.table.insertRow(0)
    assert dialog.table.rowCount() == 1

    pub.sendMessage("session.new")
    assert dialog.table.rowCount() == 0
