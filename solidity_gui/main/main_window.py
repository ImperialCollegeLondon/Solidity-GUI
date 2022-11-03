import qtawesome as qta
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
)

from .. import config
from .base_model_tree import BaseModelTree
from .control_panel import ControlPanel
from .vtk_window import VTKWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(config.APP_NAME)

        self.create_menu_bar()
        self.create_toolbar()
        self.create_main_frame()

        self.setCentralWidget(self.main_frame)

        self.show()

    def create_menu_bar(self) -> None:
        self.menu_bar = self.menuBar()

        self.menu_bar.addMenu("&File")
        self.menu_bar.addMenu("&Geometry")
        self.menu_bar.addMenu("&Mesh")
        self.menu_bar.addMenu("&Materials")
        self.menu_bar.addMenu("&Assembly")
        self.menu_bar.addMenu("&Step")
        self.menu_bar.addMenu("&Conditions")
        self.menu_bar.addMenu("&Interaction")
        self.menu_bar.addMenu("&Job")
        self.menu_bar.addMenu("&Results")
        self.menu_bar.addMenu("&Tools")
        self.menu_bar.addMenu("&View")
        self.menu_bar.addMenu("&Help")

    def create_toolbar(self) -> None:
        toolbar = QToolBar("Top toolbar")
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        self.mask_action = QAction(qta.icon("ei.adjust"), "&Mask", self)

        self.view_mode_combo = QComboBox()
        self.modules_combo = QComboBox()

        self.grid_action = QAction(qta.icon("mdi.apps"), "", self)
        self.rotation_action = QAction(
            qta.icon("mdi.rotate-3d-variant"), "&Rotation", self
        )
        self.pan_action = QAction(qta.icon("fa5s.arrows-alt"), "&Pan", self)
        self.zoom_action = QAction(qta.icon("ph.magnifying-glass-light"), "&Zoom", self)
        self.transform_xy_action = QAction(qta.icon("mdi6.axis-arrow"), "&X-Y", self)
        self.transform_xz_action = QAction(qta.icon("mdi6.axis-arrow"), "&X-Z", self)
        self.transform_yz_action = QAction(qta.icon("mdi6.axis-arrow"), "&Y-Z", self)
        self.three_d_action = QAction(qta.icon("mdi.cube-outline"), "&3D", self)
        self.two_d_action = QAction(qta.icon("fa5.square"), "&2D", self)
        self.screenshot_action = QAction(qta.icon("fa5s.camera"), "", self)
        self.clip_action = QAction(qta.icon("mdi.select-compare"), "&Clip", self)

        toolbar.addAction(self.mask_action)
        toolbar.addWidget(self.view_mode_combo)
        toolbar.addWidget(self.modules_combo)
        toolbar.addAction(self.grid_action)
        toolbar.addAction(self.rotation_action)
        toolbar.addAction(self.pan_action)
        toolbar.addAction(self.zoom_action)
        toolbar.addAction(self.transform_xy_action)
        toolbar.addAction(self.transform_xz_action)
        toolbar.addAction(self.transform_yz_action)
        toolbar.addAction(self.three_d_action)
        toolbar.addAction(self.two_d_action)
        toolbar.addAction(self.screenshot_action)
        toolbar.addAction(self.clip_action)

    def create_main_frame(self) -> None:
        self.main_frame = QFrame()
        main_layout = QVBoxLayout()

        self.create_central_frame()

        command_box = QTextEdit()
        command_box.setPlaceholderText("Type command/scripts")
        command_box.setMaximumHeight(100)

        main_layout.addWidget(self.central_frame)
        main_layout.addWidget(command_box)

        self.main_frame.setLayout(main_layout)

    def create_central_frame(self) -> None:
        self.central_frame = QFrame()
        central_layout = QHBoxLayout()

        central_layout.setSpacing(20)

        self.vtk_window = VTKWindow()
        self.control_panel = ControlPanel(self.vtk_window)
        self.model_tree = BaseModelTree(2)
        central_layout.addLayout(self.model_tree)
        central_layout.addLayout(self.control_panel)
        central_layout.addLayout(self.vtk_window)
        self.central_frame.setLayout(central_layout)
