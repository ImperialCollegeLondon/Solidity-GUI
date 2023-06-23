"""User interface elements for editing properties."""

import logging

from .forms import SimpleFormDialog
from .material import Property


class EditPropertyDialog(SimpleFormDialog):
    """Dialog for editing a material's properties."""

    def __init__(self, property: Property):
        """Create a new EditPropertyDialog.

        Args:
          property: Property to be edited
        """
        super().__init__(property.attributes, initial_data=property.data)
        self.setWindowTitle(f"Edit {property.name}")
        self.material_property = property

    def _ok_clicked(self) -> None:
        """Signal handler for clicking ok button."""
        if data := super()._ok_clicked():
            self.material_property.data = data
            self.close()

            logging.info(f"Updated {self.material_property.name} ({repr(data)})")
