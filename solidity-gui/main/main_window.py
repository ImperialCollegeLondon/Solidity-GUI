from PySide6.QtWidgets import QFrame, QHBoxLayout, QMainWindow, QToolBar, QComboBox
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
import qtawesome as qta

from .. import config
from .control_panel import ControlPanel
from .vtk_window import VTKWindow
from .base_model_tree import BaseModelTree

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(config.APP_NAME)

        layout = QHBoxLayout()
        layout.setSpacing(20)

        self.vtk_window = VTKWindow()
        self.control_panel = ControlPanel(self.vtk_window)
        self.model_tree = BaseModelTree(2)
        layout.addLayout(self.model_tree)
        layout.addLayout(self.control_panel)
        layout.addLayout(self.vtk_window)

        self._menu_bar()

        self._top_toolbar()

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
        top_toolbar.setIconSize(QSize(16, 16))
        top_toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(Qt.TopToolBarArea, top_toolbar)

        self.mask_action = QAction(qta.icon("ei.adjust"), "&Mask", self)

        self.view_mode_combo = QComboBox()
        self.modules_combo = QComboBox()

        self.grid_action = QAction(qta.icon("mdi.apps"), "", self)
        self.rotation_action = QAction(qta.icon("mdi.rotate-3d-variant"), "&Rotation", self)
        self.pan_action = QAction(qta.icon("fa5s.arrows-alt"), "&Pan", self)
        self.zoom_action = QAction(qta.icon("ph.magnifying-glass-light"), "&Zoom", self)
        self.transform_xy_action = QAction(qta.icon("mdi6.axis-arrow"), "&X-Y", self)
        self.transform_xz_action = QAction(qta.icon("mdi6.axis-arrow"), "&X-Z", self)
        self.transform_yz_action = QAction(qta.icon("mdi6.axis-arrow"), "&Y-Z", self)
        self.three_d_action = QAction(qta.icon("mdi.cube-outline"), "&3D", self)
        self.two_d_action = QAction(qta.icon("fa5.square"), "&2D", self)
        self.screenshot_action = QAction(qta.icon("fa5s.camera"), "", self)
        self.clip_action = QAction(qta.icon("mdi.select-compare"), "&Clip", self)

        top_toolbar.addAction(self.mask_action)
        top_toolbar.addWidget(self.view_mode_combo)
        top_toolbar.addWidget(self.modules_combo)
        top_toolbar.addAction(self.grid_action)
        top_toolbar.addAction(self.rotation_action)
        top_toolbar.addAction(self.pan_action)
        top_toolbar.addAction(self.zoom_action)
        top_toolbar.addAction(self.transform_xy_action)
        top_toolbar.addAction(self.transform_xz_action)
        top_toolbar.addAction(self.transform_yz_action)
        top_toolbar.addAction(self.three_d_action)
        top_toolbar.addAction(self.two_d_action)
        top_toolbar.addAction(self.screenshot_action)
        top_toolbar.addAction(self.clip_action)