"""This module provides functionality to run Solidity."""
import html
import logging
import weakref
from pathlib import Path
from threading import Event, Thread
from typing import Any, Iterable

import qtawesome as qta
from PySide6.QtCore import Qt, Signal, Slot
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
from python_on_whales import Container, docker

from ..solidity import _run_solidity, remove_container

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
    if file_paths := get_file_paths():
        # Update dialog and show
        solidity_dlg = SolidityDialog(
            parent,
            y3d_file_path=Path(file_paths[0]),
            layout_file_path=Path(file_paths[1]),
            pellet_file_path=Path(file_paths[2]),
            materials_file_path=Path(file_paths[3]),
        )
        solidity_dlg.exec_()


class SolidityDialog(QDialog):
    """A dialog for interacting with the Solidity backend and viewing the output."""

    log_updated = Signal(str, int)
    solidity_pulled = Signal()
    solidity_stopped = Signal()

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

        self._close_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self._close_btn.rejected.connect(self.close)
        layout.addWidget(self._close_btn, 0, 2, Qt.AlignmentFlag.AlignCenter)

        self._log_text_edit = QPlainTextEdit()
        self._log_text_edit.setFont(QFont("monospace"))
        self._log_text_edit.setReadOnly(True)
        layout.addWidget(self._log_text_edit, 1, 0, 1, 3)

        self.setLayout(layout)

        self._logger = self._create_logger()
        self.log_updated.connect(self._update_log_text_edit)
        self.solidity_pulled.connect(self._solidity_setup_finished)
        self.solidity_stopped.connect(self._container_finish)
        self.background_thread = BackgroundThread(self)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.background_thread.is_alive():
            event.ignore()
            return
        event.accept()

    def _solidity_setup_finished(self) -> None:
        self._stop_btn.setEnabled(True)

    def _container_finish(self) -> None:
        self._close_btn.setEnabled(True)
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

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
        self._stop_btn.setEnabled(False)
        self._close_btn.setEnabled(False)
        self._log("Setting up Solidity (this may take some time)...")
        self.stop_event = Event()
        self.background_thread.start()

    def run_solidity(self) -> Container:
        container = _run_solidity(
            self.y3d_file_path,
            self.layout_file_path,
            self.pellet_file_path,
            self.materials_file_path,
            detach=True,
        )
        assert isinstance(container, Container)
        return container

    def _stop_solidity(self) -> None:
        self._stop_btn.setEnabled(False)
        self._log("==========\nStopping Solidity...")
        self.stop_event.set()


class _DockerLogHandler(logging.Handler):
    """Send log output to a text box as well as stdout."""

    def __init__(self, dlg: SolidityDialog) -> None:
        super().__init__()

        # Use a weakref so we don't prevent dialog from being GC'd
        self._dlg = weakref.ref(dlg)

    def emit(self, record: logging.LogRecord) -> None:
        if dlg := self._dlg():
            dlg.log_updated.emit(self.format(record), record.levelno)


class BackgroundThread(Thread):
    def __init__(self, dialog: SolidityDialog, **kwargs: Any):
        self.dialog = dialog
        super().__init__(**kwargs)

    def run(self) -> None:
        try:
            container = self.dialog.run_solidity()
        except Exception as e:
            self.dialog._log(e.args[0], level=logging.ERROR)
            return
        self.dialog.solidity_pulled.emit()

        self.dialog._log("==========\nStarting Solidity...")
        from datetime import datetime
        from time import sleep

        log_timestamp = datetime.now()
        try:
            while True:
                sleep(1)
                next_timestamp = datetime.now()
                logs = docker.container.logs(
                    container, since=log_timestamp, until=next_timestamp
                )
                assert isinstance(logs, str)
                log_timestamp = next_timestamp
                if logs:
                    self.dialog._log(logs)
                if (
                    self.dialog.stop_event.is_set()
                    or container.state.status == "exited"
                ):
                    exit_code = container.state.exit_code
                    break
        finally:
            remove_container(container)

        if self.dialog.stop_event.is_set():
            self.dialog._log("==========\nStopped Solidity...")
        else:
            if exit_code:
                self.dialog._log(
                    "==========\nSolidity encountered an error and stopped...",
                    level=logging.ERROR,
                )
            else:
                self.dialog._log("==========\nSolidity finished normally...")

        self.dialog.solidity_stopped.emit()
