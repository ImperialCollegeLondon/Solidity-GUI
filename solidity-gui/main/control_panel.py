from PySide6.QtWidgets import QVBoxLayout

from .colour_select_widget import ColourSelectWidget
from .reset_view_widget import ResetViewWidget


class ControlPanel(QVBoxLayout):
    def __init__(self, vtk_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addWidget(ResetViewWidget(vtk_window))
        self.addWidget(ColourSelectWidget(vtk_window))
