from typing import Any

from PySide6.QtWidgets import QVBoxLayout

from .colour_select_widget import ColourSelectWidget
from .reset_view_widget import ResetViewWidget
from .vtk_window import VTKWindow


class ControlPanel(QVBoxLayout):
    def __init__(self, vtk_window: VTKWindow, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.addWidget(ResetViewWidget(vtk_window))
        self.addWidget(ColourSelectWidget(vtk_window))
