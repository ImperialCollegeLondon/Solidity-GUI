import logging
from pathlib import Path

from threading import Event, Thread
from typing import Any

from PySide6.QtCore import SignalInstance
from PySide6.QtWidgets import QFileDialog, QWidget

from .solidity_model import SolidityContainerManager
from .solidity_view import SolidityDialog


def get_file_paths() -> list[Path] | None:
    """Get the file paths from the user."""
    file_paths = []
    file_names = ["BST.Y3D", "layout.txt", "pellet.txt", "mat.txt"]
    for i in range(4):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setWindowTitle("Select " + file_names[i])
        if file_dialog.exec_() == QFileDialog.DialogCode.Rejected:
            return None
        file_paths.append(Path(file_dialog.selectedFiles()[0]))
    return file_paths


def run_solidity_dialog(parent: QWidget) -> None:
    """Run Solidity with the file paths selected by the user."""
    if file_paths := get_file_paths():
        # Update dialog and show
        dialog = SolidityDialog(parent)
        presenter = SolidityPresenter(dialog, file_paths)
        dialog.exec_()


# main presenter class although this interfaces tightly with a background thread
class SolidityPresenter:
    def __init__(
        self,
        dialog: SolidityDialog,
        file_paths: tuple[Path, Path, Path, Path],
    ):
        self.file_paths = file_paths

        self.dialog = dialog
        self.dialog._start_btn.clicked.connect(self._setup_solidity)
        self.dialog._stop_btn.clicked.connect(self._stop_solidity)
        self.dialog.solidity_stopped.emit()

        self._logger = self._create_logger(self.dialog.log_updated)

    def _setup_solidity(self) -> None:
        self.dialog.solidity_setup.emit()
        self.background_thread = BackgroundThread(self)
        self.background_thread.start()
        self._log("Setting up Solidity (this may take some time)...")

    def _stop_solidity(self) -> None:
        self.dialog.solidity_stopped.emit()
        self._log("==========\nStopping Solidity...")
        self.background_thread.stop_event.set()

    def _create_logger(self, signal: SignalInstance) -> logging.Logger:
        """Create a logger which outputs to stdout as well as a text box."""
        logger = logging.getLogger("Docker")
        logger.addHandler(_DockerLogHandler(signal))
        return logger

    def _log(self, output: str, level: int = logging.INFO) -> None:
        self._logger.log(level, msg=output)


class _DockerLogHandler(logging.Handler):
    """Send log output to a text box as well as stdout."""

    def __init__(self, signal: SignalInstance) -> None:
        super().__init__()

        self._signal = signal

    def emit(self, record: logging.LogRecord) -> None:
        self._signal.emit(self.format(record), record.levelno)


# this class ties together the management of the container in a background thread
# and updates to the view
class BackgroundThread(Thread):
    def __init__(self, presenter: SolidityPresenter, **kwargs: Any):
        self.presenter = presenter
        self.stop_event = Event()
        super().__init__(**kwargs)

    def run(self) -> None:
        try:
            with SolidityContainerManager(self.presenter.file_paths) as manager:
                self.presenter._log("==========\nStarting Solidity...")
                self.presenter.dialog.solidity_running.emit()
                from time import sleep

                for log_entry in manager:
                    sleep(1)
                    if log_entry:
                        self.presenter._log(log_entry)
                    if self.stop_event.is_set():
                        break

            if self.stop_event.is_set():
                self.presenter._log("==========\nStopped Solidity...")
            else:
                if manager.exit_code:
                    self.presenter._log(
                        "==========\nSolidity encountered an error and stopped...",
                        level=logging.ERROR,
                    )
                else:
                    self.presenter._log("==========\nSolidity finished normally...")

            self.presenter.dialog.solidity_stopped.emit()

        except Exception:
            self.presenter._log(
                "==========\nError running Solidity...",
                level=logging.ERROR,
            )
