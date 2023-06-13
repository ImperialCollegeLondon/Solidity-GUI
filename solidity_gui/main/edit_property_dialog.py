"""User interface elements for editing properties."""

from .forms import SimpleFormDialog
from .material import Property


class EditPropertyDialog(SimpleFormDialog):
    """Generic dialog for creating a simple geometric shape.

    Dialog contents are generated from the specified geometry.Shape.
    """

    def __init__(self, property_: Property):
        """Initialise a new dialog.

        Args:
          property_: Property which fields will be edited
        """
        super().__init__(property_.attributes, initial_data=property_.data)
        self.setWindowTitle(f"Edit {property_.name}")
        self.material_property = property_

    def _ok_clicked(self) -> None:
        """Signal handler for clicking ok button."""
        if data := super()._ok_clicked():
            self.material_property.data = data
            self.close()
