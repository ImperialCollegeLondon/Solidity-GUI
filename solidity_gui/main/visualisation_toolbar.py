"""Code to create the toolbar containing the visualisation controls."""
from typing import Any

import qtawesome as qta
from pubsub import pub
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QComboBox, QToolBar

from .. import config


class VisualisationToolbar(QToolBar):
    """A toolbar containing visualisation controls for a given VTKWindow."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create a new VisualisationToolbar."""
        super().__init__("Visualisation toolbar", *args, **kwargs)

        self.setIconSize(QSize(*config.TOOLBAR_ICON_SIZE))
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.mask_action = QAction(qta.icon("ei.adjust"), "&Mask", self)
        self.view_mode_combo = QComboBox()
        self.modules_combo = QComboBox()
        self.grid_action = QAction(qta.icon("mdi.apps"), "", self)
        self.rotate_action = QAction(qta.icon("mdi.rotate-3d-variant"), "&Rotate", self)
        self.rotate_action.setCheckable(True)
        self.pan_action = QAction(qta.icon("fa5s.arrows-alt"), "&Pan", self)
        self.pan_action.setCheckable(True)
        self.zoom_action = QAction(qta.icon("ph.magnifying-glass-light"), "&Zoom", self)
        self.zoom_action.setCheckable(True)
        self.transform_xy_action = QAction(qta.icon("mdi6.axis-arrow"), "&X-Y", self)
        self.transform_xz_action = QAction(qta.icon("mdi6.axis-arrow"), "X-&Z", self)
        self.transform_yz_action = QAction(qta.icon("mdi6.axis-arrow"), "&Y-Z", self)
        self.three_d_action = QAction(qta.icon("mdi.cube-outline"), "&3D", self)
        self.two_d_action = QAction(qta.icon("fa5.square"), "&2D", self)
        self.screenshot_action = QAction(qta.icon("fa5s.camera"), "", self)
        self.clip_action = QAction(qta.icon("mdi.select-compare"), "&Clip", self)

        # Group these QActions together so that only one can be selected at a time
        self.action_group = QActionGroup(self)
        self.action_group.addAction(self.rotate_action)
        self.action_group.addAction(self.pan_action)
        self.action_group.addAction(self.zoom_action)

        self.pan_action.setChecked(True)  # Pan is default

        self.addAction(self.mask_action)
        self.addWidget(self.view_mode_combo)
        self.addWidget(self.modules_combo)
        self.addAction(self.grid_action)
        self.addAction(self.rotate_action)
        self.addAction(self.pan_action)
        self.addAction(self.zoom_action)
        self.addAction(self.transform_xy_action)
        self.addAction(self.transform_xz_action)
        self.addAction(self.transform_yz_action)
        self.addAction(self.three_d_action)
        self.addAction(self.two_d_action)
        self.addAction(self.screenshot_action)
        self.addAction(self.clip_action)

        self.transform_xy_action.triggered.connect(self._xy_click_handler)
        self.transform_xz_action.triggered.connect(self._xz_click_handler)
        self.transform_yz_action.triggered.connect(self._yz_click_handler)

    def _xy_click_handler(self) -> None:
        pub.sendMessage(
            "camera.reorient", orientation_vector=(0, 0, 1), up_vector=(1, 0, 0)
        )

    def _xz_click_handler(self) -> None:
        pub.sendMessage(
            "camera.reorient", orientation_vector=(0, -1, 0), up_vector=(1, 0, 0)
        )

    def _yz_click_handler(self) -> None:
        pub.sendMessage(
            "camera.reorient", orientation_vector=(1, 0, 0), up_vector=(0, 1, 0)
        )
