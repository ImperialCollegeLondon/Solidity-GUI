"""Code to create the "Conditions" menu."""

from PySide6.QtWidgets import QMenu

from ..assign_conditions_dialog import AssignConditionsDialog
from ..assign_initial_conditions_dialog import AssignInitialConditionsDialog
from ..conditions_manager_dialog import ConditionsManagerDialog
from ..initial_conditions_manager_dialog import InitialConditionsManagerDialog


class ConditionsMenu(QMenu):
    """Creates the "Conditions" menu."""

    def __init__(self) -> None:
        """Create the "Conditions" menu."""
        super().__init__("&Conditions")

        self.conditions_manager_dialog = ConditionsManagerDialog()
        self.addAction(
            "Create and Edit Constant &Conditions", self.conditions_manager_dialog.open
        )
        self.initial_conditions_manager_dialog = InitialConditionsManagerDialog()
        self.addAction(
            "Create and Edit &Initial Conditions",
            self.initial_conditions_manager_dialog.open,
        )

        self.addAction("&Assign Conditions", lambda: AssignConditionsDialog().exec_())

        self.addAction(
            "A&ssign Initial Conditions",
            lambda: AssignInitialConditionsDialog().exec_(),
        )
