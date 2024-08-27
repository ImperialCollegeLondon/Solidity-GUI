"""User interface elements for editing properties."""

import logging

from .forms import SimpleFormDialog
from .material import Property, calculate_lame_constants


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
                lame_lambda, lame_mu = calculate_lame_constants(
                    data["youngs_modulus"], data["poissons_ratio"]
                )
                self.material_property.data["lame_lambda"] = lame_lambda
                self.material_property.data["lame_mu"] = lame_mu

            self.close()

            logging.info(f"Updated {self.material_property.name} ({repr(data)})")
