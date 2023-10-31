"""Simple form for creating a new initial condition."""

import logging

from solidity_gui.main.forms import SimpleFormDialog

from .initial_condition import (
    InitialCondition,
    InitialConditionForm,
    initial_condition_datastore,
)


class CreateInitialConditionDialog(SimpleFormDialog):
    """Dialog for creating an initial condition."""

    def __init__(self) -> None:
        """Initialise a new dialog."""
        super().__init__(InitialConditionForm)
        self.setWindowTitle("Create new condition")

    def _ok_clicked(self) -> None:
        """Signal handler for clicking ok button."""
        if data := super()._ok_clicked():
            condition = InitialCondition(
                data["name"],
                {key: value for key, value in data.items() if key != "name"},
            )

            initial_condition_datastore.add(condition)

            self.close()

            logging.info(f"Created initial condition {condition.name} ({data})")
