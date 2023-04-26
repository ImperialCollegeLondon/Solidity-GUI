"""Code to create the toolbar containing the visualisation controls."""
from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenuBar

from .assign_properties_dialog import AssignPropertiesDialog
from .drillco_dialog import DrillCoDialog
from .materials_manager_dialog import MaterialsManagerDialog
from .solidity_file_generator import generate_y3d_file


class MenuBar(QMenuBar):
    """A menu bar containing menu items for the Solidity GUI."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create a new VisualisationToolbar."""
        super().__init__(*args, **kwargs)

        file_menu = self.addMenu("&File")
        geometry_menu = self.addMenu("&Geometry")
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

        self.materials_manager_dialog = MaterialsManagerDialog()
        materials_manager_action = QAction("Create and Edit &Materials", self)
        materials_manager_action.triggered.connect(  # type: ignore[attr-defined]
            self.materials_manager_dialog.open
        )
        self.materials_menu.addAction(materials_manager_action)

        self.assign_properties_dialog = AssignPropertiesDialog()
        assign_properties_action = QAction("&Assign Properties", self)
        assign_properties_action.triggered.connect(  # type: ignore[attr-defined]
            self.assign_properties_dialog.open
        )
        self.materials_menu.addAction(assign_properties_action)

        drill_action = QAction("Create &drill system", self)
        drill_action.triggered.connect(  # type: ignore[attr-defined]
            lambda: DrillCoDialog().exec_()
        )
        geometry_menu.addAction(drill_action)

        export_bst_action = QAction("&Export BST", self)
        export_bst_action.triggered.connect(generate_y3d_file)
        file_menu.addAction(export_bst_action)
