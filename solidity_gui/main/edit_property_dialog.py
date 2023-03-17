"""User interface elements for editing properties."""

from .forms import SimpleFormDialog
from .material import DensityForm, Property


class EditPropertyDialog(SimpleFormDialog):
    """Generic dialog for creating a simple geometric shape.

    Dialog contents are generated from the specified geometry.Shape.
    """

    def __init__(self, property: Property):
        """Initialise a new dialog.

        Args:
          property: Property which fields will be edited
        """
        super().__init__(DensityForm)
        self.setWindowTitle(f"Edit {property.name}")

    def _ok_clicked(self) -> None:
        """Signal handler for clicking ok button."""
        if data := super()._ok_clicked():
            print(data)
            self.close()
