"""Test case for CreateInitialConditionDialog."""
from solidity_gui.main.create_initial_condition_dialog import (
    CreateInitialConditionDialog,
)
from solidity_gui.main.initial_condition import (
    InitialCondition,
    InitialConditionForm,
    initial_condition_datastore,
)


def test_ok_clicked(qtbot):
    """Test values in form are correctly parsed and Condition is added to datastore."""
    # Instantiate dialog
    dialog = CreateInitialConditionDialog()

    # Fill in form fields with test data
    data = dict(name="test_condition", x=1.0, y=2.0, z=3.0)
    form_info = InitialConditionForm().form_info(data=data)
    dialog.form_info = form_info

    dialog._ok_clicked()

    # Check that InitialCondition is added to datastore
    assert len(initial_condition_datastore) == 1
    condition = list(initial_condition_datastore.values())[0]
    assert isinstance(condition, InitialCondition)
    assert condition.properties["x"] == 1.0
    assert condition.properties["y"] == 2.0
    assert condition.properties["z"] == 3.0
