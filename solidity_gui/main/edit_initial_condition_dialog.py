"""Dialog for adding simple geometric shapes."""

import logging

from .forms import SimpleFormDialog
from .initial_condition import InitialCondition, InitialConditionForm


class EditInitialConditionDialog(SimpleFormDialog):
    """Dialog for editing a material's properties."""

    def __init__(self, condition: InitialCondition):
        """Create a new EditPropertyDialog.

        Args:
          condition: Condition to be edited
        """
        super().__init__(
            InitialConditionForm,
            initial_data=condition.properties | dict(name=condition.name),
        )
        self.setWindowTitle(f"Edit {condition.name}")
        self.condition = condition

    def _ok_clicked(self) -> None:
        """Signal handler for clicking ok button."""
        if data := super()._ok_clicked():
            self.condition.properties = {
                key: value for key, value in data.items() if key != "name"
            }
            self.condition.name = data["name"]
            self.close()

            logging.info(f"Updated condition {self.condition.name} ({data})")
