"""Tests for solidity_gui.main.drillco_dialog module."""
from solidity_gui.main.drillco_dialog import (
    BIT_FACE_HEIGHT,
    GAP_LENGTH,
    INSERT_DISPLACEMENT_FACTOR,
    INSERT_LENGTH_FACTOR,
    DrillCoDialog,
    DrillCoForm,
)
from solidity_gui.main.forms.info import FormInfo
from solidity_gui.main.geometry import Component


def test_drill_co_dialog(qtbot):
    """Test instantiation of DrillCoDialog."""
    dialog = DrillCoDialog()
    assert dialog.form_class is DrillCoForm
    assert isinstance(dialog.form_info, FormInfo)


def test_drill_co_dialog_ok_clicked(qtbot, send_message_mock):
    """Check ok button event handler of DrillCoDialog."""
    dialog = DrillCoDialog()

    data = dict(
        bit=dict(width=1.0, length=5.0, inserts=dict(number=2, width=0.15)),
        piston=dict(length_ratio=1.5, width=1.5),
    )
    form_info = DrillCoForm().form_info(data=data)
    dialog.form_info = form_info

    dialog._ok_clicked()
    send_message_mock.assert_any_call(
        "geometry.update",
        component=Component(
            "box",
            "ground",
            dict(x0=[0, -1, -1], extents=[2, 2, 2]),
        ),
    )
    bit_distance = data["bit"]["length"] + GAP_LENGTH + BIT_FACE_HEIGHT
    send_message_mock.assert_any_call(
        "geometry.update",
        component=Component(
            "drillbit",
            "bit",
            dict(
                insert_number=data["bit"]["inserts"]["number"],
                x0=[-bit_distance, 0, 0],
                axis=[data["bit"]["length"], 0, 0],
                face_height=BIT_FACE_HEIGHT,
                radius=data["bit"]["width"] / 2,
                insert_radius=data["bit"]["inserts"]["width"] / 2,
                insert_displacement=data["bit"]["width"]
                / 2
                * INSERT_DISPLACEMENT_FACTOR,
                insert_length=BIT_FACE_HEIGHT * INSERT_LENGTH_FACTOR,
            ),
        ),
    )
    piston_length = data["bit"]["length"] * data["piston"]["length_ratio"]
    piston_distance = bit_distance + piston_length + GAP_LENGTH
    send_message_mock.assert_any_call(
        "geometry.update",
        component=Component(
            "cylinder",
            "piston",
            dict(
                x0=[-piston_distance, 0, 0],
                axis=[piston_length, 0, 0],
                radius=data["piston"]["width"] / 2,
            ),
        ),
    )
