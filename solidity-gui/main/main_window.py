from PySide6.QtWidgets import QFrame, QHBoxLayout, QMainWindow, QToolBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from .. import config
from .control_panel import ControlPanel
from .vtk_window import VTKWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(config.APP_NAME)

        layout = QHBoxLayout()
        layout.setSpacing(20)

        self.vtk_window = VTKWindow()
        self.control_panel = ControlPanel(self.vtk_window)
        layout.addLayout(self.control_panel)
        layout.addLayout(self.vtk_window)

        self._menu_bar()

        self._top_toolbar()
        self._left_toolbar()

        self.frame = QFrame()
        self.frame.setLayout(layout)
        self.setCentralWidget(self.frame)
        self.show()

    def _menu_bar(self):
        self.menu_bar = self.menuBar()
    
        file_menu = self.menu_bar.addMenu("&File")
        gemoetry_menu = self.menu_bar.addMenu("&Gemoetry")
        mesh_menu = self.menu_bar.addMenu("&Mesh")
        materials_menu = self.menu_bar.addMenu("&Materials")
        assembly_menu = self.menu_bar.addMenu("&Assembly")
        step_menu = self.menu_bar.addMenu("&Step")
        conditions_menu = self.menu_bar.addMenu("&Conditions")
        interaqctions_menu = self.menu_bar.addMenu("&Interaction")
        job_menu = self.menu_bar.addMenu("&Job")
        results_menu = self.menu_bar.addMenu("&Results")
        tools_menu = self.menu_bar.addMenu("&Tools")
        view_menu = self.menu_bar.addMenu("&View")
        help_menu = self.menu_bar.addMenu("&Help")

    def _top_toolbar(self):
        top_toolbar = QToolBar("Top toolbar")
        self.addToolBar(Qt.TopToolBarArea, top_toolbar)

        self.mask_action = QAction("&Mask", self)
        self.view_mode_action = QAction("&View Mode", self)
        self.modules_action = QAction("&Modules", self)
        self.mask_action = QAction("&Mask", self)
        top_toolbar.addAction(self.mask_action)

    def _left_toolbar(self):
        left_toolbar = QToolBar("Left toolbar")
        self.addToolBar(Qt.LeftToolBarArea, left_toolbar)
