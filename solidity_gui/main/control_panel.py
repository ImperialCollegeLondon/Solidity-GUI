"""Code for a control panel to select surface colour and to reset view orientation."""
from functools import partial
from typing import Any

from pubsub import pub
from PySide6.QtWidgets import QPushButton, QVBoxLayout

from .add_shape_button import AddShapeButton
from .colour_select_widget import ColourSelectWidget
from .create_mesh_button import CreateMeshButton


class ControlPanel(QVBoxLayout):
    """A control panel for selecting surface colour and reset view orientation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create a ControlPanel.

        Args:
            vtk_window: The VTKWindow which the widgets will control
        """
        super().__init__(*args, **kwargs)
        reset_button = QPushButton("Reset view")
        reset_button.clicked.connect(partial(pub.sendMessage, "camera.reset"))

        self.addWidget(reset_button)
        self.addWidget(ColourSelectWidget())
        self.addWidget(AddShapeButton("ball"))
        self.addWidget(AddShapeButton("box"))
        self.addWidget(AddShapeButton("cone"))
        self.addWidget(AddShapeButton("cylinder"))
        self.addWidget(CreateMeshButton())
