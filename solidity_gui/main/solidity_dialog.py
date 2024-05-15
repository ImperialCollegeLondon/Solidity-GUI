"""This module provides functionality to run Solidity."""

import html
import logging
import weakref
from collections.abc import Iterable
from pathlib import Path

import qtawesome as qta
from pubsub import pub
from PySide6.QtCore import QFileInfo, Qt, Signal, Slot
from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)
from python_on_whales.exceptions import DockerException

from .error_message import display_error_message

OutputStream = Iterable[tuple[str, bytes]]


def get_file_paths() -> list[Path] | None:
    """Get the file paths from the user."""
    file_paths = []
    file_dialog = QFileDialog()
    file_dialog.setFileMode(QFileDialog.ExistingFiles)

    # Dialog for selecting BST.Y3D file
    file_dialog.setWindowTitle("Select BST.Y3D")
    if file_dialog.exec_() == QFileDialog.DialogCode.Rejected:
        return None
    file_paths.append(Path(file_dialog.selectedFiles()[0]))
    path = QFileInfo(file_paths[0]).path()

    # Dialog for selecting mat.txt file
    file_dialog.setWindowTitle("Select mat.txt")
    if file_dialog.exec_() == QFileDialog.DialogCode.Rejected:
        return None
    file_paths.append(Path(file_dialog.selectedFiles()[0]))

    for file in ["layout.txt", "pellet.txt"]:
        file_path = Path(path, file)
        try:
            file_path.resolve(strict=True)
        except FileNotFoundError as e:
            display_error_message(f"File not found: {e.filename}")
            return None
        file_paths.append(file_path)
    return file_paths


def run_solidity(parent: QWidget) -> None:
    """Run Solidity with the file paths selected by the user."""
    global _solidity_dlg
    if file_paths := get_file_paths():
        if not _solidity_dlg:
            # Create dialog
            _solidity_dlg = SolidityDialog(parent)

        # Update dialog and show
        _solidity_dlg.update_dialog(
            y3d_file_path=file_paths[0],
            layout_file_path=file_paths[2],
            pellet_file_path=file_paths[3],
            materials_file_path=file_paths[1],
        )
        _solidity_dlg.exec_()


class SolidityDialog(QDialog):
    """A dialog for interacting with the Solidity backend and viewing the output."""

    log_updated = Signal(str, int)

    def __init__(self, parent: QWidget | None) -> None:
        """Create a new SolidityDialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.resize(350, 500)

        layout = QGridLayout()
        self._start_btn = QPushButton(qta.icon("ei.play"), "Start Solidity")
        self._start_btn.clicked.connect(self._start_solidity)
        layout.addWidget(self._start_btn, 0, 0, Qt.AlignmentFlag.AlignCenter)
        self._stop_btn = QPushButton(qta.icon("ei.stop"), "Stop Solidity")
        self._stop_btn.clicked.connect(self._stop_solidity)
        self._stop_btn.setEnabled(False)
        layout.addWidget(self._stop_btn, 0, 1, Qt.AlignmentFlag.AlignCenter)

        cancel_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.rejected.connect(self.hide)
        layout.addWidget(cancel_btn, 0, 2, Qt.AlignmentFlag.AlignCenter)

        self._log_text_edit = QPlainTextEdit()
        self._log_text_edit.setFont(QFont("monospace"))
        self._log_text_edit.setReadOnly(True)
        layout.addWidget(self._log_text_edit, 1, 0, 1, 3)

        self.setLayout(layout)

        pub.subscribe(self._on_docker_pulled, "docker.pulled")
        pub.subscribe(self._on_docker_started, "docker.started")
        pub.subscribe(self._on_docker_stopped, "docker.stopped")
        pub.subscribe(self._on_docker_error, "docker.error")
        pub.subscribe(self._log, "docker.output")

        self._logger = self._create_logger()
        self.log_updated.connect(self._update_log_text_edit)

    def update_dialog(
        self,
        y3d_file_path: Path,
        layout_file_path: Path,
        pellet_file_path: Path,
        materials_file_path: Path,
    ) -> None:
        """Update parameters."""
        self.y3d_file_path = y3d_file_path
        self.layout_file_path = layout_file_path
        self.pellet_file_path = pellet_file_path
        self.materials_file_path = materials_file_path

    def closeEvent(self, evt: QCloseEvent) -> None:
        """Hide the dialog if the user tries to close it."""
        self.hide()
        evt.ignore()

    def hide(self) -> None:
        """Hide the dialog."""
        super().hide()
        pub.sendMessage("docker.stop")

    def _create_logger(self) -> logging.Logger:
        """Create a logger which outputs to stdout as well as a text box."""
        logger = logging.getLogger("Docker")
        logger.addHandler(_DockerLogHandler(self))
        return logger

    def _log(self, output: str, level: int = logging.INFO) -> None:
        self._logger.log(level, msg=output)

    @Slot()
    def _update_log_text_edit(self, msg: str, level: int) -> None:
        if level <= logging.INFO:
            self._log_text_edit.appendPlainText(msg)
        else:
            self._log_text_edit.appendHtml(
                f'<font color="red">{html.escape(msg)}</font>'
            )

    def _start_solidity(self) -> None:
        self._start_btn.setEnabled(False)
        self._log("Setting up Solidity (this may take some time)...")
        pub.sendMessage("docker.pull")

    def _on_docker_pulled(self) -> None:
        self._log("Starting Solidity...")
        pub.sendMessage(
            "docker.start",
            y3d_file_path=self.y3d_file_path,
            layout_file_path=self.layout_file_path,
            pellet_file_path=self.pellet_file_path,
            materials_file_path=self.materials_file_path,
        )

    def _on_docker_started(self) -> None:
        self._stop_btn.setEnabled(True)
        self._log("Solidity started\n==========")

    def _stop_solidity(self) -> None:
        self._stop_btn.setEnabled(False)
        self._log("==========\nStopping Solidity...")
        pub.sendMessage("docker.stop")

    def _on_docker_stopped(self, return_code: int) -> None:
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._log(f"Solidity stopped (exit code: {return_code})")

    def _on_docker_error(self, error: BaseException) -> None:
        if isinstance(error, DockerException):
            # Pretty printing for Docker errors
            self._log(
                f"Error occurred while running Docker command: {error.docker_command}",
                level=logging.ERROR,
            )
        else:
            self._log(f"Error occurred: {repr(error)}", level=logging.ERROR)


class _DockerLogHandler(logging.Handler):
    """Send log output to a text box as well as stdout."""

    def __init__(self, dlg: SolidityDialog) -> None:
        super().__init__()

        # Use a weakref so we don't prevent dialog from being GC'd
        self._dlg = weakref.ref(dlg)

    def emit(self, record: logging.LogRecord) -> None:
        if dlg := self._dlg():
            dlg.log_updated.emit(self.format(record), record.levelno)


_solidity_dlg: SolidityDialog | None = None
