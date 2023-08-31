"""Dialog for adding simple geometric shapes."""

import logging

from .condition import Condition, ConditionForm
from .forms import SimpleFormDialog


class EditConditionDialog(SimpleFormDialog):
    """Dialog for editing a material's properties."""

    def __init__(self, condition: Condition):
        """Create a new EditPropertyDialog.

        Args:
          condition: Condition to be edited
        """
        super().__init__(ConditionForm, initial_data=condition.properties)
        self.setWindowTitle(f"Edit {condition.name}")
        self.condition = condition

    def _ok_clicked(self) -> None:
        """Signal handler for clicking ok button."""
        if data := super()._ok_clicked():
            self.condition.properties = data
            self.close()

            logging.info(f"Updated {self.condition.name} ({repr(data)})")
