"""Tests for solidity_gui.main.drillco_dialog module."""
from unittest.mock import patch

from solidity_gui.main.condition import (
    condition_assignment_datastore,
    condition_datastore,
)
from solidity_gui.main.drillco_dialog import DrillCoDialog, DrillCoForm
from solidity_gui.main.forms.info import FormInfo
from solidity_gui.main.material import material_assignment_datastore, material_datastore


def test_drill_co_dialog(qtbot):
    """Test instantiation of DrillCoDialog."""
    dialog = DrillCoDialog()
    assert dialog.form_class is DrillCoForm
    assert isinstance(dialog.form_info, FormInfo)


TEST_DATA = (dict(a=0, b=1), dict(c=2, d=3), [4, 5], [6], [7, 8, 9])


@patch(
    "solidity_gui.main.drillco_dialog.create_drillco_system", lambda *args: TEST_DATA
)
def test_drill_co_dialog_ok_clicked(qtbot, send_message_mock):
    """Check ok button event handler of DrillCoDialog.

    The responsibilities of this function are to broadcast and store the outputs of the
    create_drillco_system function so we don't need to work with real data. Instead we
    patch out that function and inject some arbitrary data then check the correct
    messages are sent and datastores updated.
    """
    dialog = DrillCoDialog()

    data = dict(
        bit=dict(width=1.0, length=5.0, inserts=dict(length=1, width=0.15)),
        piston=dict(length=5.0, width=1.5),
        ground=dict(width=1.0, height=1.0),
    )
    form_info = DrillCoForm().form_info(data=data)
    dialog.form_info = form_info

    dialog._ok_clicked()

    # the mesh_datastore would usually be updated by a handler of the
    # add_component.finish signal
    for mesh_name, obj in TEST_DATA[0].items():
        send_message_mock.assert_any_call(
            "add_component.finish", mesh_name=mesh_name, obj=obj
        )

    # for everything else the datastores are updated directly
    assert material_datastore == {
        i: value for i, value in enumerate(TEST_DATA[1].values())
    }
    assert material_assignment_datastore == {
        i: value for i, value in enumerate(TEST_DATA[2])
    }
    assert condition_datastore == {i: value for i, value in enumerate(TEST_DATA[3])}
    assert condition_assignment_datastore == {
        i: value for i, value in enumerate(TEST_DATA[4])
    }
