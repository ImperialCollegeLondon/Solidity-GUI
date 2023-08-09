"""Code for the main window containing all the frames and menus of the GUI."""
import logging

from pubsub import pub
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QMainWindow

from .. import config
from .control_panel import ControlPanel
from .geometry import Component
from .menu_bar import MenuBar
from .trial_expiry import quit_if_expired
from .uncaught_exceptions import set_uncaught_exception_handler
from .visualisation_toolbar import VisualisationToolbar
from .vtk_window import VTKWindow


def _log_geometry_update(mesh_name: str, component: Component) -> None:
    """Log when new components are added to the geometry."""
    logging.info(f'Added new component "{component.label}" (type: {component.shape})')


class MainWindow(QMainWindow):
    """Main window containing all the GUI frames and menus."""

    def __init__(self) -> None:
        """Create new MainWindow."""
        super().__init__()

        set_uncaught_exception_handler(self)

        self.setWindowTitle(config.APP_NAME)

        menu_bar = MenuBar()
        self.setMenuBar(menu_bar)
        self.setCentralWidget(self.create_main_frame())

        # create the toolbar containing the various visualisation buttons
        visualisation_toolbar = VisualisationToolbar()
        self.addToolBar(Qt.TopToolBarArea, visualisation_toolbar)

        logging.info("Creating main window")

        pub.subscribe(_log_geometry_update, "geometry.update")

    def show(self) -> None:
        """Show the main window."""
        super().show()

        # For when running a trial version
        quit_if_expired()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Send message when window is closed."""
        super().closeEvent(event)
        pub.sendMessage("window.close")

        logging.info("Main window closed")

    def create_main_frame(self) -> QFrame:
        """Create the main frame.

        This is called and created inside the main frame.

        This contains the side control panel, and the VTK window.
        """
        main_frame = QFrame()
        central_layout = QHBoxLayout()

        central_layout.setSpacing(config.CENTRAL_LAYOUT_SPACING)

        self.vtk_window = VTKWindow()
        self.control_panel = ControlPanel()
        central_layout.addLayout(self.control_panel)
        central_layout.addWidget(self.vtk_window)
        main_frame.setLayout(central_layout)

        return main_frame
