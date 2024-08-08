"""Code for the main window containing all the frames and menus of the GUI."""

import logging

from pubsub import pub
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow

from .. import config
from .components import Component
from .mac_restriction import quit_if_no_access
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

        logging.info("Creating main window")

        pub.subscribe(_log_geometry_update, "geometry.update")

    def show(self) -> None:
        """Show the main window."""
        super().show()

        # Access verification
        quit_if_no_access()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Send message when window is closed."""
        super().closeEvent(event)
        pub.sendMessage("window.close")

        logging.info("Main window closed")
