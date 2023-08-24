"""Dialog for adding simple geometric shapes."""

import logging

from .condition import Condition
from .dialog import SimpleFormDialog


class EditConditionDialog(SimpleFormDialog):
    """Dialog for editing a material's properties."""

    def __init__(self, condition: Condition):
        """Create a new EditPropertyDialog.

        Args:
          condition: Condition to be edited
        """
        # super().__init__(condition.attributes, initial_data=condition.data)
        super().__init__()
        self.setWindowTitle(f"Edit {condition.name}")
        self.material_property = condition

    def _ok_clicked(self) -> None:
        """Signal handler for clicking ok button."""
        if data := super()._ok_clicked():
            # self.material_property.data = data
            self.close()

            logging.info(f"Updated {self.material_property.name} ({repr(data)})")
