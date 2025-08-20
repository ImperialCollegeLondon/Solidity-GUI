"""Code to create the "Job" menu."""

from functools import partial

from PySide6.QtWidgets import QMenu

from ..menus.menu_utils import create_action
from ..solidity_dialog import run_solidity


class JobMenu(QMenu):
    """Creates the "Job" menu."""

    def __init__(self) -> None:
        """Create the "Job" menu."""
        super().__init__("&Job")

        self.addAction(
            create_action(self, "&Run Solidity", partial(run_solidity, self))
        )
