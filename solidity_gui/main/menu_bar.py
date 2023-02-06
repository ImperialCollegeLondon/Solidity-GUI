"""Code to create the toolbar containing the visualisation controls."""
from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenuBar

from .materials_manager_dialog import MaterialsManagerDialog


class MenuBar(QMenuBar):
    """A menu bar containing menu items for the Solidity GUI."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create a new VisualisationToolbar."""
        super().__init__(*args, **kwargs)

        materials_manager_action = QAction("&Manager", self)
        materials_manager_action.triggered.connect(
            self._materials_manager_click_handler
        )

        self.addMenu("&File")
        self.addMenu("&Geometry")
        self.addMenu("&Mesh")
        self.materials_menu = self.addMenu("Materia&ls")
        self.addMenu("&Assembly")
        self.addMenu("&Step")
        self.addMenu("&Conditions")
        self.addMenu("&Interaction")
        self.addMenu("&Job")
        self.addMenu("&Results")
        self.addMenu("&Tools")
        self.addMenu("&View")
        self.addMenu("&Help")

        self.materials_menu.addAction(materials_manager_action)

        self.materials_manager_dialog = MaterialsManagerDialog()

    def _materials_manager_click_handler(self) -> None:
        self.materials_manager_dialog.open()
