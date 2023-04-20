"""Code for the main window containing all the frames and menus of the GUI."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QMainWindow, QTextEdit, QVBoxLayout

from .. import config
from .base_model_tree import BaseModelTree
from .control_panel import ControlPanel
from .menu_bar import MenuBar
from .uncaught_exceptions import set_uncaught_exception_handler
from .visualisation_toolbar import VisualisationToolbar
from .vtk_window import VTKWindow
from .y3d_file_generator import Y3DFileGenerator


class MainWindow(QMainWindow):
    """Main window containing all the GUI frames and menus."""

    def __init__(self) -> None:
        """Create new MainWindow."""
        super().__init__()

        set_uncaught_exception_handler(self)

        self.setWindowTitle(config.APP_NAME)

        menu_bar = MenuBar()
        self.setMenuBar(menu_bar)
        self.create_main_frame()
        # create the toolbar containing the various visualisation buttons
        visualisation_toolbar = VisualisationToolbar()
        self.addToolBar(Qt.TopToolBarArea, visualisation_toolbar)

        self.setCentralWidget(self.main_frame)

        input_file_generator = Y3DFileGenerator()
        input_file_generator.generate_y3d_file()

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
        central_layout.addWidget(self.vtk_window)
        self.central_frame.setLayout(central_layout)
