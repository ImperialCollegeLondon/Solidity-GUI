"""Code to create the "Materials" menu."""

from PySide6.QtWidgets import QMenu

from ..assign_properties_dialog import AssignPropertiesDialog
from ..joint_materials_dialog import JointMaterialsDialog
from ..materials_manager_dialog import MaterialsManagerDialog
from .menu_utils import create_action


class MaterialsMenu(QMenu):
    """Creates the "Materials" menu."""

    def __init__(self) -> None:
        """Create the "Materials" menu."""
        super().__init__("&Materials")

        self.materials_manager_dialog = MaterialsManagerDialog()
        self.addAction(
            create_action(
                self,
                "Create and Edit &Materials",
                self.materials_manager_dialog.open,
            )
        )
        self.addAction("&Assign Properties", lambda: AssignPropertiesDialog().exec_())
        self.addAction(
            "&Joint Material Properties", lambda: JointMaterialsDialog().exec_()
        )
