"""Code to create the "Mesh" menu."""

from typing import cast

from pubsub import pub
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

from ..assign_mesh_size_dialog import AssignMeshSizeDialog
from ..mesh_size_dialog import MeshSizeDialog
from .menu_utils import create_action


class MeshMenu(QMenu):
    """Creates the "Mesh" menu."""

    def __init__(self) -> None:
        """Create the "Mesh" menu."""
        super().__init__("&Mesh")

        # cast below is used to correct an erroneous type hint from PySide
        # QMenu.addAction is typed as returning None when it actually returns QAction
        self._mesh_size_action = cast(
            QAction,
            self.addAction(
                "&Assign Mesh Sizes", lambda: AssignMeshSizeDialog().exec_()
            ),
        )

        # Create mesh
        self._mesh_create_action = create_action(
            self, "Create &Mesh", lambda: MeshSizeDialog().exec_()
        )
        self.addAction(self._mesh_create_action)
        self._mesh_create_action.setEnabled(False)
        pub.subscribe(self._enable_mesh_create_action, "create_mesh_button.enable")

    def _enable_mesh_create_action(self, enabled: bool) -> None:
        self._mesh_create_action.setEnabled(enabled)
