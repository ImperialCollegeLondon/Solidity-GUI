"""This module provides functionality to run Solidity."""
import html
import logging

import qtawesome as qta
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)


class SolidityDialog(QDialog):
    """A dialog for interacting with the Solidity backend and viewing the output."""

    # these signals define the API usable by the presenter
    # in this case we have to used signals because updates come from a background thread
    # and signals let us interrupt the GUI main loop for instant updates
    # more generally the api could just be function calls
    log_updated = Signal(str, int)
    solidity_setup = Signal()
    solidity_running = Signal()
    solidity_stopped = Signal()

    def __init__(
        self,
        parent: QWidget | None,
    ) -> None:
        """Create a new SolidityDialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.resize(350, 500)

        layout = QGridLayout()
        self._start_btn = QPushButton(qta.icon("ei.play"), "Start Solidity")
        layout.addWidget(self._start_btn, 0, 0, Qt.AlignmentFlag.AlignCenter)
        self._stop_btn = QPushButton(qta.icon("ei.stop"), "Stop Solidity")
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

        # wire up the signals and their handlers
        self.solidity_setup.connect(self._setup)
        self.solidity_running.connect(self._running)
        self.solidity_stopped.connect(self._stopped)
        self.log_updated.connect(self._update_log_text_edit)

    # the next four methods are the "set" methods
    def _setup(self) -> None:
        # put the GUI into the correct state for Solidity setup
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        self._close_btn.setEnabled(False)
        self.closeable = False

    def _running(self) -> None:
        # put the GUI into the correct state for Solidity running
        self._start_btn.setEnabled(False)
        self._close_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self.closeable = False

    def _stopped(self) -> None:
        # put the GUI into the correct state for Solidity not running
        self._start_btn.setEnabled(True)
        self._close_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self.closeable = True

    @Slot()
    def _update_log_text_edit(self, msg: str, level: int) -> None:
        if level <= logging.INFO:
            self._log_text_edit.appendPlainText(msg)
        else:
            self._log_text_edit.appendHtml(
                f'<font color="red">{html.escape(msg)}</font>'
            )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.closeable:
            event.accept()
        else:
            event.ignore()
