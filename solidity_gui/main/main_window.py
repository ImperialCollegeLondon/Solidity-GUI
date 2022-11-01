from PySide6.QtWidgets import QFrame, QHBoxLayout, QMainWindow

from .. import config
from .control_panel import ControlPanel
from .vtk_window import VTKWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(config.APP_NAME)

        layout = QHBoxLayout()
        layout.setSpacing(20)

        self.vtk_window = VTKWindow()
        self.control_panel = ControlPanel(self.vtk_window)
        layout.addLayout(self.control_panel)
        layout.addLayout(self.vtk_window)

        self.frame = QFrame()
        self.frame.setLayout(layout)
        self.setCentralWidget(self.frame)
        self.show()
