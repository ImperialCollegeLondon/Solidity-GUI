"""Code to create the toolbar containing the visualisation controls."""

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Any, cast

from meshio import Mesh
from pubsub import pub
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtWidgets import QMenu, QMenuBar

from .add_shape_dialogue import AddShapeDialog
from .assign_conditions_dialog import AssignConditionsDialog
from .assign_initial_conditions_dialog import AssignInitialConditionsDialog
from .assign_mesh_size_dialog import AssignMeshSizeDialog
from .assign_properties_dialog import AssignPropertiesDialog
from .conditions_manager_dialog import ConditionsManagerDialog
from .geometry import SHAPES
from .initial_conditions_manager_dialog import InitialConditionsManagerDialog
from .joint_materials_dialog import JointMaterialsDialog
from .load_geometry import load_geometry
from .materials_manager_dialog import MaterialsManagerDialog
from .problem_data import ProblemDataDialog
from .mesh_size_dialog import MeshSizeDialog
from .session_handling import load_session, save_session, start_new_session
from .solidity_dialog import run_solidity
from .solidity_file_generator import generate_output_files


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
        geometry_menu = self.addMenu("&Geometry")
        materials_menu = self.addMenu("Materia&ls")
        conditions_menu = self.addMenu("&Conditions")
        mesh_menu = self.addMenu("&Mesh")
        job_menu = self.addMenu("&Job")

        geometry_menu.addAction(self._create_shape_action("ball"))
        geometry_menu.addAction(self._create_shape_action("box"))
        geometry_menu.addAction(self._create_shape_action("cone"))
        geometry_menu.addAction(self._create_shape_action("cylinder"))

        self.materials_manager_dialog = MaterialsManagerDialog()
        materials_menu.addAction(
            self._create_action(
                "Create and Edit &Materials", self.materials_manager_dialog.open
            )
        )

        self.conditions_manager_dialog = ConditionsManagerDialog()
        conditions_menu.addAction(
            "Create and Edit Constant &Conditions", self.conditions_manager_dialog.open
        )
        self.initial_conditions_manager_dialog = InitialConditionsManagerDialog()
        conditions_menu.addAction(
            "Create and Edit &Initial Conditions",
            self.initial_conditions_manager_dialog.open,
        )

        materials_menu.addAction(
            "&Assign Properties", lambda: AssignPropertiesDialog().exec_()
        )
        materials_menu.addAction(
            "&Joint Material Properties", lambda: JointMaterialsDialog().exec_()
        )

        conditions_menu.addAction(
            "&Assign Conditions", lambda: AssignConditionsDialog().exec_()
        )

        conditions_menu.addAction(
            "A&ssign Initial Conditions",
            lambda: AssignInitialConditionsDialog().exec_(),
        )

        # cast below is used to correct an erroneous type hint from PySide
        # QMenu.addAction is typed as returning None when it actually returns QAction
        self._mesh_size_action = cast(
            QAction,
            mesh_menu.addAction(
                "&Assign Mesh Sizes", lambda: AssignMeshSizeDialog().exec_()
            ),
        )

        # Create mesh
        self._mesh_create_action = self._create_action(
            "Create &Mesh", lambda: MeshSizeDialog().exec_()
        )
        mesh_menu.addAction(self._mesh_create_action)
        self._mesh_create_action.setEnabled(False)
        pub.subscribe(self._enable_mesh_create_action, "create_mesh_button.enable")

        # New session
        file_menu.addAction(self._create_action("&New Session", start_new_session))

        self.save_session_action = QAction("&Save Session", self)
        self.save_session_action.triggered.connect(partial(save_session, self))
        self.save_session_action.setEnabled(False)
        file_menu.addAction(self.save_session_action)

        file_menu.addAction(
            self._create_action("&Load Session", partial(load_session, self))
        )

        # Problem Data
        file_menu.addAction(
            self._create_action("&Problem Data", lambda: ProblemDataDialog().exec_())
        )

        self.solidity_files_action = self._create_action(
            "&Create Solidity Input Files", generate_output_files
        )
        self.solidity_files_action.setEnabled(False)
        file_menu.addAction(self.solidity_files_action)

        file_menu.addAction(self._create_action("E&xit", QGuiApplication.quit))

        # There's currently no way to remove meshes, so just enable the menu entry when
        # the first component is added
        pub.subscribe(self._enable_exporting_files, "add_component.finish")

        pub.subscribe(self._enable_exporting_files, "session.enable_export_bst")

        pub.subscribe(self._disable_exporting_files, "session.new")

        job_menu.addAction(
            self._create_action("&Run Solidity", partial(run_solidity, self))
        )

        for item in extra_menu_items:
            menu = self._get_or_create_menu(item.menu_title)
            menu.addAction(self._create_action(item.action_label, item.callback))

        import_geometry_action = QAction("&Import Geometry from file", self)
        import_geometry_action.triggered.connect(partial(load_geometry, self))
        geometry_menu.addAction(import_geometry_action)

    def _disable_exporting_files(self) -> None:
        self.solidity_files_action.setEnabled(False)
        self.save_session_action.setEnabled(False)

    def _enable_exporting_files(self, mesh_name: str, obj: Mesh) -> None:
        self.solidity_files_action.setEnabled(True)
        self.save_session_action.setEnabled(True)

    def _get_or_create_menu(self, title: str) -> QMenu:
        for menu in self.findChildren(QMenu):
            if menu.title() == title:
                return menu
        return self.addMenu(title)

    def _create_action(self, label: str, callback: Callable) -> QAction:
        action = QAction(label, self)
        action.triggered.connect(callback)
        return action

    def _create_shape_action(self, label: str) -> QAction:
        def callback() -> None:
            AddShapeDialog(SHAPES[label]).exec_()

        return self._create_action(f"Add {label.capitalize()}", callback)

    def _enable_mesh_create_action(self, enabled: bool) -> None:
        self._mesh_create_action.setEnabled(enabled)
