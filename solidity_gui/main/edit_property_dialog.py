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
        if (data := super()._ok_clicked()) is not None:
            self.material_property.data = data

            # If editing Elasticity, calculate Lame's Constants from Young's Modulus
            # and Poisson's Ratio.
            # Formula for Lame's Constants:
            # https://encyclopediaofmath.org/wiki/Lam%C3%A9_constants
            if self.material_property.name == "Elasticity":
                E = data["youngs_modulus"]
                nu = data["poissons_ratio"]
                data["lame_lambda"] = E * nu / ((1 + nu) * (1 - 2 * nu))
                data["lame_mu"] = E / (2 * (1 + nu))

            self.close()

            logging.info(f"Updated {self.material_property.name} ({repr(data)})")
