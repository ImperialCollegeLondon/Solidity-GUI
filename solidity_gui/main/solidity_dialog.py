"""This module provides functionality to run Solidity."""
import html
import logging
import weakref
from pathlib import Path
from typing import Iterable

import qtawesome as qta
from pubsub import pub
from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont
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

OutputStream = Iterable[tuple[str, bytes]]


def get_file_paths() -> list[str] | None:
    """Get the file paths from the user."""
    file_paths = []
    file_names = ["BST.Y3D", "layout.txt", "pellet.txt", "mat.txt"]
    for i in range(4):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setWindowTitle("Select " + file_names[i])
        if file_dialog.exec_() == QFileDialog.DialogCode.Rejected:
            return None
        file_paths.append(file_dialog.selectedFiles()[0])
    return file_paths


def run_solidity(parent: QWidget) -> None:
    """Run Solidity with the file paths selected by the user."""
    global _solidity_dlg
    if file_paths := get_file_paths():
        _solidity_dlg = SolidityDialog(
            parent,
            y3d_file_path=Path(file_paths[0]),
            layout_file_path=Path(file_paths[1]),
            pellet_file_path=Path(file_paths[2]),
            materials_file_path=Path(file_paths[3]),
        )
        _solidity_dlg.exec_()


class _LogUpdateThread(QThread):
    log_updated = Signal(str)

    def __init__(self, parent: QObject, output_stream: OutputStream) -> None:
        super().__init__(None)
        self._output_stream = output_stream

    def run(self) -> None:
        for _, line in self._output_stream:
            # Strip final newline char
            self.log_updated.emit(line[:-1].decode(errors="replace"))


class SolidityDialog(QDialog):
    """A dialog for interacting with the Solidity backend and viewing the output."""

    log_updated = Signal(str, int)

    def __init__(
        self,
        parent: QWidget | None,
        y3d_file_path: Path,
        layout_file_path: Path,
        pellet_file_path: Path,
        materials_file_path: Path,
    ) -> None:
        """Create a new SolidityDialog.

        Args:
            parent: Parent widget
            y3d_file_path: Path to Y3D file (BST.Y3D)
            layout_file_path: Path to file with format for elements and particles
                            (layout.txt)
            pellet_file_path: Path to file with elements and particles (pellet.txt)
            materials_file_path: Path to materials file (mat.txt)
        """
        super().__init__(parent)
        self.resize(350, 500)

        self.y3d_file_path = y3d_file_path
        self.layout_file_path = layout_file_path
        self.pellet_file_path = pellet_file_path
        self.materials_file_path = materials_file_path

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
        self._log("Downloading Solidity (this may take some time)...")
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


_solidity_dlg: SolidityDialog
