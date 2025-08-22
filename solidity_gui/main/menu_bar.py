"""Code to create the toolbar containing the visualisation controls."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from PySide6.QtWidgets import QMenu, QMenuBar

from .menus.conditions_menu import ConditionsMenu
from .menus.file_menu import FileMenu
from .menus.geometry_menu import GeometryMenu
from .menus.job_menu import JobMenu
from .menus.materials_menu import MaterialsMenu
from .menus.menu_utils import create_action
from .menus.mesh_menu import MeshMenu


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

        self.addMenu(FileMenu())
        self.addMenu(GeometryMenu())
        self.addMenu(MaterialsMenu())
        self.addMenu(ConditionsMenu())
        self.addMenu(MeshMenu())
        self.addMenu(JobMenu())

        for item in extra_menu_items:
            menu = self._get_or_create_menu(item.menu_title)
            menu.addAction(create_action(menu, item.action_label, item.callback))

    def _get_or_create_menu(self, title: str) -> QMenu:
        for menu in self.findChildren(QMenu):
            if menu.title() == title:
                return menu
        return self.addMenu(title)
