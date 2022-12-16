"""Code for a control panel to select surface colour and to reset view orientation."""
from typing import Any

from PySide6.QtWidgets import QVBoxLayout

from .add_mesh_button import AddMeshButton
from .colour_select_widget import ColourSelectWidget
from .reset_view_widget import ResetViewWidget
from .vtk_window import VTKWindow


class ControlPanel(QVBoxLayout):
    """A control panel for selecting surface colour and reset view orientation."""

    def __init__(self, vtk_window: VTKWindow, *args: Any, **kwargs: Any) -> None:
        """Create a ControlPanel.

        Args:
            vtk_window: The VTKWindow which the widgets will control
        """
        super().__init__(*args, **kwargs)
        self.addWidget(ResetViewWidget(vtk_window))
        self.addWidget(ColourSelectWidget())
        self.addWidget(AddMeshButton("ball"))
        self.addWidget(AddMeshButton("box"))
