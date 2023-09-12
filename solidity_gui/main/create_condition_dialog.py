"""Simple form for creating a new material."""

import logging

from solidity_gui.main.forms import SimpleFormDialog

from .condition import Condition, ConditionForm, condition_datastore


class CreateConditionDialog(SimpleFormDialog):
    """Dialog for creating a condition."""

    def __init__(self) -> None:
        """Initialise a new dialog."""
        super().__init__(ConditionForm)
        self.setWindowTitle("Create new condition")

    def _ok_clicked(self) -> None:
        """Signal handler for clicking ok button."""
        if data := super()._ok_clicked():
            condition = Condition(name=data["name"])
            condition.properties = {
                key: value for key, value in data.items() if key != "name"
            }

            condition_datastore.add(condition)

            self.close()

            logging.info(f"Created condition {condition.name} ({data})")
