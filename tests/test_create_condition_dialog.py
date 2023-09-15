"""Test case for CreateConditionDialog."""
from solidity_gui.main.condition import Condition, ConditionForm, condition_datastore
from solidity_gui.main.create_condition_dialog import CreateConditionDialog


def test_ok_clicked():
    """Test values in form are correctly parsed and Condition is added to datastore."""
    # Instantiate dialog
    dialog = CreateConditionDialog()

    # Fill in form fields with test data
    data = dict(
        name="test_condition",
        acceleration_x=1.0,
        acceleration_y=2.0,
        acceleration_z=3.0,
        force_x=4.0,
        force_y=5.0,
        force_z=6.0,
        velocity_x=7.0,
        velocity_y=8.0,
        velocity_z=9.0,
        velocity_constraint_x=1,
        velocity_constraint_y=1,
        velocity_constraint_z=1,
    )
    form_info = ConditionForm().form_info(data=data)
    dialog.form_info = form_info

    dialog._ok_clicked()

    # Check that Condition is added to datastore
    assert len(condition_datastore) == 1
    condition = list(condition_datastore.values())[0]
    assert isinstance(condition, Condition)
    assert condition.properties["acceleration_x"] == 1.0
    assert condition.properties["acceleration_y"] == 2.0
    assert condition.properties["acceleration_z"] == 3.0
    assert condition.properties["force_x"] == 4.0
    assert condition.properties["force_y"] == 5.0
    assert condition.properties["force_z"] == 6.0
    assert condition.properties["velocity_x"] == 7.0
    assert condition.properties["velocity_y"] == 8.0
    assert condition.properties["velocity_z"] == 9.0
    assert condition.properties["velocity_constraint_x"] == 1
    assert condition.properties["velocity_constraint_y"] == 1
    assert condition.properties["velocity_constraint_z"] == 1
