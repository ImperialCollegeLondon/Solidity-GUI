"""Code to create the "File" menu."""

from functools import partial

from meshio import Mesh
from pubsub import pub
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMenu

from ..problem_data import ProblemDataDialog
from ..session_handling import load_session, save_session, start_new_session
from ..solidity_file_generator import generate_output_files
from .menu_utils import create_action


class FileMenu(QMenu):
    """Creates the "File" menu."""

    def __init__(self) -> None:
        """Create the "File" menu."""
        super().__init__("&File")
        self.addAction(create_action(self, "&New Session", start_new_session))

        self.save_session_action = create_action(
            self, "&Save Session", partial(save_session, self)
        )
        self.save_session_action.setEnabled(False)
        self.addAction(self.save_session_action)

        self.addAction(
            create_action(self, "&Load Session", partial(load_session, self))
        )
        self.addSeparator()

        self.addAction(
            create_action(self, "&Problem Data", lambda: ProblemDataDialog().exec_())
        )
        self.addSeparator()

        self.solidity_files_action = create_action(
            self, "&Create Solidity Input Files", lambda: generate_output_files()
        )
        self.solidity_files_action.setEnabled(False)
        self.addAction(self.solidity_files_action)
        self.addSeparator()

        self.addAction(create_action(self, "E&xit", QGuiApplication.quit))

        pub.subscribe(self._enable_exporting_files, "add_component.finish")
        pub.subscribe(self._enable_exporting_files, "session.enable_export_bst")
        pub.subscribe(self._disable_exporting_files, "session.new")

    def _disable_exporting_files(self) -> None:
        self.solidity_files_action.setEnabled(False)
        self.save_session_action.setEnabled(False)

    def _enable_exporting_files(self, mesh_name: str, obj: Mesh) -> None:
        self.solidity_files_action.setEnabled(True)
        self.save_session_action.setEnabled(True)
