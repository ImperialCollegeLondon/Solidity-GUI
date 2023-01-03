"""Code for the main window containing all the frames and menus of the GUI."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QMainWindow, QTextEdit, QVBoxLayout

from .. import config
from .base_model_tree import BaseModelTree
from .control_panel import ControlPanel
from .visualisation_toolbar import VisualisationToolbar
from .vtk_window import VTKWindow


class MainWindow(QMainWindow):
    """Main window containing all the GUI frames and menus."""

    def __init__(self) -> None:
        """Create new MainWindow."""
        super().__init__()

        self.setWindowTitle(config.APP_NAME)

        self.create_menu_bar()
        self.create_main_frame()
        # create the toolbar containing the various visualisation buttons
        visualisation_toolbar = VisualisationToolbar()
        self.addToolBar(Qt.TopToolBarArea, visualisation_toolbar)

        self.setCentralWidget(self.main_frame)

    def create_menu_bar(self) -> None:
        """Create the menu bar at the top of the main window."""
        self.menu_bar = self.menuBar()

        self.menu_bar.addMenu("&File")
        self.menu_bar.addMenu("&Geometry")
        self.menu_bar.addMenu("&Mesh")
        self.menu_bar.addMenu("Materia&ls")
        self.menu_bar.addMenu("&Assembly")
        self.menu_bar.addMenu("&Step")
        self.menu_bar.addMenu("&Conditions")
        self.menu_bar.addMenu("&Interaction")
        self.menu_bar.addMenu("&Job")
        self.menu_bar.addMenu("&Results")
        self.menu_bar.addMenu("&Tools")
        self.menu_bar.addMenu("&View")
        self.menu_bar.addMenu("&Help")

    def create_main_frame(self) -> None:
        """Create the main frame of the window.

        This contains the central frame, and the text box.
        """
        self.main_frame = QFrame()
        main_layout = QVBoxLayout()

        self.create_central_frame()

        command_box = QTextEdit()
        command_box.setPlaceholderText("Type command/scripts")
        command_box.setMaximumHeight(config.COMMAND_BOX_MAXIMUM_HEIGHT)

        main_layout.addWidget(self.central_frame)
        main_layout.addWidget(command_box)

        self.main_frame.setLayout(main_layout)

    def create_central_frame(self) -> None:
        """Create the central frame.

        This is called and created inside the main frame.

        This contains the side control panel, and the VTK window.
        """
        self.central_frame = QFrame()
        central_layout = QHBoxLayout()

        central_layout.setSpacing(config.CENTRAL_LAYOUT_SPACING)

        self.vtk_window = VTKWindow()
        self.control_panel = ControlPanel()
        self.model_tree = BaseModelTree(2)
        central_layout.addLayout(self.model_tree)
        central_layout.addLayout(self.control_panel)
        central_layout.addLayout(self.vtk_window)
        self.central_frame.setLayout(central_layout)
