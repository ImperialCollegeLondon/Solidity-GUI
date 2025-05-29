"""Code for the main window containing all the frames and menus of the GUI."""

import logging
import sys

from pubsub import pub
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QMessageBox, QStatusBar

from .. import config
from .components import Component
from .logger_bar import QTextEditLogger
from .mac_restriction import is_mac_address_allowed
from .menu_bar import MenuBar
from .uncaught_exceptions import set_uncaught_exception_handler
from .visualisation_toolbar import VisualisationToolbar
from .vtk_window import VTKWindow


def _log_geometry_update(mesh_name: str, component: Component) -> None:
    """Log when new components are added to the geometry."""
    logging.info(
        f'Added new component to gmsh process "{mesh_name}" (type: {component.shape})'
    )


class MainWindow(QMainWindow):
    """Main window containing all the GUI frames and menus."""

    def __init__(self) -> None:
        """Create new MainWindow."""
        super().__init__()

        set_uncaught_exception_handler(self)

        self.setWindowTitle(config.APP_NAME)

        menu_bar = MenuBar()
        self.setMenuBar(menu_bar)
        self.vtk_window = VTKWindow()
        self.setCentralWidget(self.vtk_window)

        # create the toolbar containing the various visualisation buttons
        visualisation_toolbar = VisualisationToolbar()
        self.addToolBar(Qt.TopToolBarArea, visualisation_toolbar)

        # create the status bar
        status_bar = QStatusBar(self)
        log_bar = QTextEditLogger(status_bar)
        logging.getLogger().addHandler(log_bar)
        status_bar.addPermanentWidget(log_bar.widget, 1)
        self.setStatusBar(status_bar)

        logging.info("Creating main window")

        pub.subscribe(_log_geometry_update, "geometry.update")

    def show(self) -> None:
        """Show the main window."""
        allowed, mac = is_mac_address_allowed()
        if not allowed:
            QMessageBox.critical(
                self,
                "Computer not authorized",
                f"Your MAC address '{mac}' is not allowed to use this copy of "
                "Solidity GUI",
            )
            sys.exit(1)

        super().show()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Send message when window is closed."""
        super().closeEvent(event)
        pub.sendMessage("window.close")

        logging.info("Main window closed")
