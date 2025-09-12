"""This module provides functionality to run Solidity."""

import html
import logging
import weakref
from collections.abc import Iterable
from os import cpu_count
from pathlib import Path
from typing import cast

import qtawesome as qta
from pubsub import pub
from PySide6.QtCore import QFileInfo, Signal, Slot
from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from python_on_whales.exceptions import DockerException

from .error_message import display_error_message
from .material import material_datastore

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
    """Show the Solidity dialog."""
    global _solidity_dlg
    if not _solidity_dlg:
        # Create dialog
        _solidity_dlg = SolidityDialog(parent)
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
        layout = QVBoxLayout()
        self.setWindowTitle("Run Solidity")

        self.y3d_file_path: Path | None = None
        self.layout_file_path: Path | None = None
        self.pellet_file_path: Path | None = None
        self.materials_file_path: Path | None = None

        self._select_files_btn = QPushButton("Select Input Files")
        self._select_files_btn.clicked.connect(self._select_input_files)
        layout.addWidget(self._select_files_btn)

        self._setup_parameter_sweep_ui(layout)

        self._start_btn = QPushButton(qta.icon("ei.play"), "Start Solidity")
        self._start_btn.clicked.connect(self._start_solidity)
        self._start_btn.setEnabled(False)
        layout_solver_controls = QHBoxLayout()
        layout_solver_controls.addWidget(self._start_btn)
        self._stop_btn = QPushButton(qta.icon("ei.stop"), "Stop Solidity")
        self._stop_btn.clicked.connect(self._stop_solidity)
        self._stop_btn.setEnabled(False)
        layout_solver_controls.addWidget(self._stop_btn)

        self._cancel_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self._cancel_btn.rejected.connect(self.hide)
        layout_solver_controls.addWidget(self._cancel_btn)
        layout.addLayout(layout_solver_controls)

        # CPU selection spin box
        layout_cpu_controls = QHBoxLayout()
        self._cpu_label = QLabel("CPU Cores:")
        self._cpu_spin_box = QSpinBox()
        self._cpu_spin_box.setRange(1, cpu_count())
        self._cpu_spin_box.setValue(cpu_count())
        self._cpu_spin_box.setToolTip("Number of CPU cores for running Solidity")
        layout_cpu_controls.addWidget(self._cpu_label)
        layout_cpu_controls.addWidget(self._cpu_spin_box)
        layout.addLayout(layout_cpu_controls)

        self._log_text_edit = QPlainTextEdit()
        self._log_text_edit.setFont(QFont("monospace"))
        self._log_text_edit.setReadOnly(True)
        layout.addWidget(self._log_text_edit)

        self.setLayout(layout)

        pub.subscribe(self._on_docker_pulled, "docker.pulled")
        pub.subscribe(self._on_docker_started, "docker.started")
        pub.subscribe(self._on_docker_stopped, "docker.stopped")
        pub.subscribe(self._on_docker_error, "docker.error")
        pub.subscribe(self._log, "docker.output")

        self._logger = self._create_logger()
        self.log_updated.connect(self._update_log_text_edit)

    def _select_input_files(self) -> None:
        """Select input files for Solidity."""
        file_paths = get_file_paths()
        if file_paths:
            self.y3d_file_path = file_paths[0]
            self.layout_file_path = file_paths[2]
            self.pellet_file_path = file_paths[3]
            self.materials_file_path = file_paths[1]
            self._start_btn.setEnabled(True)
            self._log("Input files selected.")
        else:
            self._log("File selection cancelled or incomplete.")

    def _setup_parameter_sweep_ui(self, layout: QVBoxLayout) -> None:
        """Set up the UI elements for parameter sweep."""
        self._sweep_checkbox = QCheckBox("Parameter Sweep (Young's Modulus)")
        self._sweep_material_combo = QComboBox()
        self._sweep_material_combo.setEnabled(False)
        self._sweep_start = QDoubleSpinBox()
        self._sweep_start.setPrefix("Start: ")
        self._sweep_start.setMinimum(0.0)
        self._sweep_start.setMaximum(1e18)
        self._sweep_start.setEnabled(False)
        self._sweep_stop = QDoubleSpinBox()
        self._sweep_stop.setPrefix("Stop: ")
        self._sweep_stop.setMinimum(0.0)
        self._sweep_stop.setMaximum(1e18)
        self._sweep_stop.setEnabled(False)
        self._sweep_step = QDoubleSpinBox()
        self._sweep_step.setPrefix("Step: ")
        self._sweep_step.setMinimum(0.0)
        self._sweep_step.setMaximum(1e18)
        self._sweep_step.setEnabled(False)

        self._populate_sweep_material_combo()
        self._sweep_material_combo.currentIndexChanged.connect(
            self._update_sweep_values
        )
        self._sweep_checkbox.stateChanged.connect(self._toggle_sweep_controls)

        layout_parameter_sweep = QVBoxLayout()
        layout_parameter_sweep.addWidget(self._sweep_checkbox)
        layout_parameter_sweep.addWidget(self._sweep_material_combo)
        layout.addLayout(layout_parameter_sweep)

        layout_parameter_values = QHBoxLayout()
        layout_parameter_values.addWidget(self._sweep_start)
        layout_parameter_values.addWidget(self._sweep_stop)
        layout_parameter_values.addWidget(self._sweep_step)
        layout.addLayout(layout_parameter_values)

    def _toggle_sweep_controls(self, _: int) -> None:
        state = self._sweep_checkbox.isChecked()
        self._sweep_material_combo.setEnabled(state)
        self._sweep_start.setEnabled(state)
        self._sweep_stop.setEnabled(state)
        self._sweep_step.setEnabled(state)

    def _populate_sweep_material_combo(self) -> None:
        self._sweep_material_combo.clear()
        for key, material in material_datastore.items():
            if material.properties["elasticity"].enabled:
                self._sweep_material_combo.addItem(material.name, userData=key)

        self._update_sweep_values()

    def _update_sweep_values(self) -> None:
        material_name = self._sweep_material_combo.currentData()
        if material_name is None:
            self._sweep_start.setValue(0.0)
            return

        material = material_datastore[material_name]

        elasticity_property = material.properties["elasticity"]
        data = elasticity_property.data or {}
        if "youngs_modulus" in data:
            youngs_modulus = cast(float, data["youngs_modulus"])
        else:
            youngs_modulus = cast(
                float, elasticity_property.default_data["youngs_modulus"]
            )
        self._sweep_start.setValue(youngs_modulus)
        self._sweep_stop.setValue(1e18)
        self._sweep_step.setValue(youngs_modulus / 10 if youngs_modulus > 0 else 1.0)

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
        if not all(
            [
                self.y3d_file_path,
                self.layout_file_path,
                self.pellet_file_path,
                self.materials_file_path,
            ]
        ):
            display_error_message("Please select all input files before starting.")
            return
        self._start_btn.setEnabled(False)
        self._cpu_spin_box.setEnabled(False)
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
            num_cpus=self._cpu_spin_box.value(),
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
        self._cpu_spin_box.setEnabled(True)
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
