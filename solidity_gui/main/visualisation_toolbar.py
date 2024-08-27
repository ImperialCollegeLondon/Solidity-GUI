"""Code to create the toolbar containing the visualisation controls."""

from functools import partial
from typing import Any

import qtawesome as qta
from pubsub import pub
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolBar, QWidget

from .. import config
from .mesh_mask_combobox import MeshMaskComboBox


class VisualisationToolbar(QToolBar):
    """A toolbar containing visualisation controls for a given VTKWindow."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create a new VisualisationToolbar."""
        super().__init__("Visualisation toolbar", *args, **kwargs)

        self.setIconSize(QSize(*config.TOOLBAR_ICON_SIZE))
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # Some not-so-nice PySide code to add the mask icon + label
        iconwidget = qta.IconWidget()
        mask_icon = qta.icon("ei.adjust")
        iconwidget.setIcon(mask_icon)
        iconwidgetholder = QWidget()
        mask_label_icon_layout = QHBoxLayout()
        mask_label_icon_layout.setContentsMargins(0, 0, 5, 0)
        mask_label_icon_layout.addWidget(iconwidget)
        mask_label_icon_layout.addWidget(QLabel("Mask:"))
        iconwidgetholder.setLayout(mask_label_icon_layout)
        self.addWidget(iconwidgetholder)

        mask_combo_box = MeshMaskComboBox("mesh.mask")

        self.pan_action = QAction(qta.icon("fa5s.arrows-alt"), "&Pan", self)
        self.pan_action.setCheckable(True)
        self.rotate_action = QAction(qta.icon("mdi.rotate-3d-variant"), "&Rotate", self)
        self.rotate_action.setCheckable(True)
        self.zoom_action = QAction(qta.icon("ph.magnifying-glass-light"), "&Zoom", self)
        self.zoom_action.setCheckable(True)
        self.transform_xy_action = QAction(qta.icon("mdi6.axis-arrow"), "&X-Y", self)
        self.transform_xz_action = QAction(qta.icon("mdi6.axis-arrow"), "X-&Z", self)
        self.transform_yz_action = QAction(qta.icon("mdi6.axis-arrow"), "&Y-Z", self)
        self.reset_view_action = QAction(qta.icon("fa.arrows"), "&Reset view", self)

        # Group these QActions together so that only one can be selected at a time
        self.action_group = QActionGroup(self)
        self.action_group.addAction(self.pan_action)
        self.action_group.addAction(self.rotate_action)
        self.action_group.addAction(self.zoom_action)
        self.action_group.triggered.connect(self._change_interact_mode)

        self.pan_action.setChecked(True)  # Pan is default

        self.addWidget(mask_combo_box)

        self.addAction(self.pan_action)
        self.addAction(self.rotate_action)
        self.addAction(self.zoom_action)
        self.addAction(self.transform_xy_action)
        self.addAction(self.transform_xz_action)
        self.addAction(self.transform_yz_action)
        self.addAction(self.reset_view_action)

        self.transform_xy_action.triggered.connect(self._xy_click_handler)
        self.transform_xz_action.triggered.connect(self._xz_click_handler)
        self.transform_yz_action.triggered.connect(self._yz_click_handler)
        self.reset_view_action.triggered.connect(
            partial(pub.sendMessage, "camera.reset")
        )

    def _change_interact_mode(self, action: QAction) -> None:
        pub.sendMessage(
            "window.change_mode", mode=action.text().replace("&", "").lower()
        )

    def _mask_click_handler(self) -> None:
        pub.sendMessage("mesh.mask")

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
