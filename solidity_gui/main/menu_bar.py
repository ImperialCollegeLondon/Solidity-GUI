"""Code to create the toolbar containing the visualisation controls."""
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Any

from meshio import Mesh
from pubsub import pub
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtWidgets import QMenu, QMenuBar

from .assign_conditions import assign_conditions
from .assign_properties_dialog import AssignPropertiesDialog
from .materials_manager_dialog import MaterialsManagerDialog
from .solidity_dialog import run_solidity
from .solidity_file_generator import generate_y3d_file


@dataclass
class ExtraMenuItem:
    """Holds the data needed to create a new menu item."""

    menu_title: str
    action_label: str
    callback: Callable


extra_menu_items: list[ExtraMenuItem] = []
"""Hook that can be added to by plugins to specify additional menu items."""


class MenuBar(QMenuBar):
    """A menu bar containing menu items for the Solidity GUI."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create a new VisualisationToolbar."""
        super().__init__(*args, **kwargs)

        file_menu = self.addMenu("&File")
        self.addMenu("&Geometry")
        self.materials_menu = self.addMenu("Materia&ls")
        self.conditions_menu = self.addMenu("&Conditions")
        job_menu = self.addMenu("&Job")

        self.materials_manager_dialog = MaterialsManagerDialog()
        materials_manager_action = QAction("Create and Edit &Materials", self)
        materials_manager_action.triggered.connect(self.materials_manager_dialog.open)
        self.materials_menu.addAction(materials_manager_action)

        assign_properties_action = QAction("&Assign Properties", self)
        assign_properties_action.triggered.connect(
            lambda: AssignPropertiesDialog().exec_()
        )
        self.materials_menu.addAction(assign_properties_action)

        conditions_action = QAction("&Assign Conditions", self)
        conditions_action.triggered.connect(assign_conditions)
        self.conditions_menu.addAction(conditions_action)

        self.export_bst_action = QAction("&Export BST", self)
        self.export_bst_action.setEnabled(False)
        self.export_bst_action.triggered.connect(generate_y3d_file)
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(QGuiApplication.quit)
        file_menu.addAction(self.export_bst_action)
        file_menu.addAction(exit_action)

        # There's currently no way to remove meshes, so just enable the menu entry when
        # the first component is added
        pub.subscribe(self._enable_export_bst, "add_component.finish")

        run_solidity_action = QAction("&Run Solidity", self)
        run_solidity_action.triggered.connect(partial(run_solidity, self))
        job_menu.addAction(run_solidity_action)

        for item in extra_menu_items:
            menu = self._get_or_create_menu(item.menu_title)
            action = QAction(item.action_label, self)
            action.triggered.connect(item.callback)  # type: ignore[attr-defined]
            menu.addAction(action)

    def _enable_export_bst(self, mesh_name: str, obj: Mesh) -> None:
        self.export_bst_action.setEnabled(True)

    def _get_or_create_menu(self, title: str) -> QMenu:
        for menu in self.findChildren(QMenu):
            if menu.title() == title:
                return menu
        return self.addMenu(title)
