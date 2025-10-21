"""Module for storing the Problem Data and the associated dialog."""

import logging

from marshmallow import validate

from solidity_gui.main.forms.forms import Form

from .control import control_datastore
from .forms import SimpleFormDialog
from .forms.fields import ComboBoxField, FloatField, IntField, LargeFloatField


class ProblemDataForm(Form):
    """Form for collecting Problem Data."""

    maximum_time_steps = IntField(
        display_name="Maximum-Number-Time-Steps", validators=[validate.Range(min=0)]
    )
    gravity_x = FloatField(display_name="Gravity in X direction")
    gravity_y = FloatField(display_name="Gravity in Y direction")
    gravity_z = FloatField(display_name="Gravity in Z direction")
    time_step = LargeFloatField(display_name="Time-Step")
    output_frequency = IntField(
        display_name="Output-Frequency", validators=[validate.Range(min=0)]
    )
    cell_size = FloatField(display_name="Cell-Size")
    maximum_contacting_couples = IntField(
        display_name="Maximum-Contacting-Couples", validators=[validate.Range(min=0)]
    )
    buffer_size_nbs = FloatField(display_name="Buffer-Size-for-NBS")
    restart_save_number = IntField(
        display_name="Restart Save Number", validators=[validate.Range(min=0)]
    )
    element_type = ComboBoxField(items=["Linear"], display_name="Element-type")
    gravity_setting_stage = FloatField(display_name="Gravity setting stage (s)")
    load_ramping_stage = FloatField(display_name="Load ramping stage (s)")
    load_constant_stage = FloatField(display_name="Load constant stage (s)")
    unload_ramping_stage = FloatField(display_name="Unload ramping stage (s)")
    stand_off_distance = FloatField(display_name="Stand off distance (s)")
    jet_load_ramping = FloatField(display_name="Jet load ramping (s)")


class ProblemDataDialog(SimpleFormDialog):
    """Dialog for editing the problem data."""

    def __init__(self) -> None:
        """Initialise a new dialog."""
        super().__init__(ProblemDataForm, initial_data=control_datastore)

    def _ok_clicked(self) -> None:
        if data := super()._ok_clicked():
            control_datastore.update(**data)
            self.close()

            logging.info(f"Problem Data updated ({data})")
