"""Test the JointMaterialsDialog class."""

from solidity_gui.main.joint_materials_dialog import JointMaterialsDialog


def test_joint_materials_clear_new_session(qtbot):
    """Test the _clear_assignments method of the JointMaterialsDialog class."""
    from pubsub import pub

    dialog = JointMaterialsDialog()
    dialog.table.insertRow(0)
    assert dialog.table.rowCount() == 1

    pub.sendMessage("session.new")
    assert dialog.table.rowCount() == 0
