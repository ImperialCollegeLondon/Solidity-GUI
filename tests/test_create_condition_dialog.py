"""Test case for CreateConditionDialog."""

from solidity_gui.main.condition import Condition, ConditionForm, condition_datastore
from solidity_gui.main.create_condition_dialog import CreateConditionDialog


def test_ok_clicked(qtbot):
    """Test values in form are correctly parsed and Condition is added to datastore."""
    # Instantiate dialog
    dialog = CreateConditionDialog()

    # Fill in form fields with test data
    data = dict(
        name="test_condition",
        x_value=1.0,
        y_value=2.0,
        z_value=3.0,
        constraint_x="Force",
        constraint_y="Acceleration",
        constraint_z="Velocity",
    )
    form_info = ConditionForm().form_info(data=data)
    dialog.form_info = form_info

    dialog._ok_clicked()

    # Check that Condition is added to datastore
    assert len(condition_datastore) == 1
    condition = list(condition_datastore.values())[0]
    print(condition.properties)
    assert isinstance(condition, Condition)
    assert condition.properties["x_value"] == 1.0
    assert condition.properties["y_value"] == 2.0
    assert condition.properties["z_value"] == 3.0
    assert condition.properties["constraint_x"] == "Force"
    assert condition.properties["constraint_y"] == "Acceleration"
    assert condition.properties["constraint_z"] == "Velocity"
