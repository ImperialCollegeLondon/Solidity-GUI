from PySide6.QtWidgets import QApplication

from .main.main_window import MainWindow

app = QApplication()
window = MainWindow()

app.exec()
