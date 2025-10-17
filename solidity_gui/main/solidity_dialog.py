"""This module provides functionality to run Solidity."""

import concurrent.futures
import html
import logging
import shutil
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
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from python_on_whales import docker
from python_on_whales.exceptions import DockerException

from .error_message import display_error_message
from .material import Property, calculate_lame_constants, material_datastore
from .solidity_file_generator import generate_output_files

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
    job_done_signal = Signal(dict)

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

        self._setup_parameter_sweep_ui(layout)

        self._setup_cpu_ui(layout)

        # Progress bar for sweep jobs
        self._progress_bar = QProgressBar()
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        layout.addWidget(self._progress_bar)

        # Job list widget for selecting jobs
        self._job_list_widget = QListWidget()
        self._job_list_widget.setMinimumHeight(80)
        layout.addWidget(self._job_list_widget)

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
        self.job_done_signal.connect(self._on_job_done)

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
        """Set up the UI elements for parameter sweep using a QGroupBox."""
        from PySide6.QtWidgets import QGroupBox

        self._sweep_group = QGroupBox("Parameter Sweep (Young's Modulus)")
        self._sweep_group.setCheckable(True)
        self._sweep_group.setChecked(False)
        self._sweep_group.setToolTip(
            "Enable this option to run a parameter sweep over Young's modulus. "
            "All sweep controls will be enabled, and input file selection will be "
            "disabled."
        )
        sweep_layout = QVBoxLayout()

        self._sweep_material_combo = QComboBox()
        self._sweep_start = QDoubleSpinBox()
        self._sweep_start.setPrefix("Start: ")
        self._sweep_start.setMinimum(0.0)
        self._sweep_start.setMaximum(1e18)
        self._sweep_stop = QDoubleSpinBox()
        self._sweep_stop.setPrefix("Stop: ")
        self._sweep_stop.setMinimum(0.0)
        self._sweep_stop.setMaximum(1e18)
        self._sweep_step = QDoubleSpinBox()
        self._sweep_step.setPrefix("Step: ")
        self._sweep_step.setMinimum(0.0)
        self._sweep_step.setMaximum(1e18)

        self._populate_sweep_material_combo()
        self._sweep_material_combo.currentIndexChanged.connect(
            self._update_sweep_values
        )
        self._sweep_group.toggled.connect(self._toggle_sweep_controls)

        sweep_layout.addWidget(self._sweep_material_combo)

        # Add file selectors for layout.txt and pellet.txt
        self._layout_file_label = QLabel("No layout.txt selected")
        self._layout_file_btn = QPushButton("Select layout.txt")
        self._layout_file_btn.clicked.connect(self._select_layout_file)
        layout_file_row = QHBoxLayout()
        layout_file_row.addWidget(self._layout_file_btn)
        layout_file_row.addWidget(self._layout_file_label)
        sweep_layout.addLayout(layout_file_row)

        self._pellet_file_label = QLabel("No pellet.txt selected")
        self._pellet_file_btn = QPushButton("Select pellet.txt")
        self._pellet_file_btn.clicked.connect(self._select_pellet_file)
        pellet_file_row = QHBoxLayout()
        pellet_file_row.addWidget(self._pellet_file_btn)
        pellet_file_row.addWidget(self._pellet_file_label)
        sweep_layout.addLayout(pellet_file_row)

        param_values_layout = QHBoxLayout()
        param_values_layout.addWidget(self._sweep_start)
        param_values_layout.addWidget(self._sweep_stop)
        param_values_layout.addWidget(self._sweep_step)
        sweep_layout.addLayout(param_values_layout)
        self._sweep_group.setLayout(sweep_layout)
        layout.addWidget(self._sweep_group)

    def _select_layout_file(self) -> None:
        """Select layout.txt file for Solidity."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select layout.txt", "", "Text Files (*.txt)"
        )
        if file_path:
            self.layout_file_path = Path(file_path)
            self._layout_file_label.setText(str(file_path))
        else:
            self._layout_file_label.setText("No layout.txt selected")

    def _select_pellet_file(self) -> None:
        """Select pellet.txt file for Solidity."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select pellet.txt", "", "Text Files (*.txt)"
        )
        if file_path:
            self.pellet_file_path = Path(file_path)
            self._pellet_file_label.setText(str(file_path))
        else:
            self._pellet_file_label.setText("No pellet.txt selected")

    def _setup_cpu_ui(self, layout: QVBoxLayout) -> None:
        layout_cpu_controls = QHBoxLayout()

        self._select_files_btn = QPushButton("Select Input Files")
        self._select_files_btn.clicked.connect(self._select_input_files)
        layout_cpu_controls.addWidget(self._select_files_btn)

        self._cpu_label = QLabel("CPU Cores:")
        self._cpu_spin_box = QSpinBox()
        self._cpu_spin_box.setRange(1, cpu_count())
        self._cpu_spin_box.setValue(cpu_count())
        self._cpu_spin_box.setToolTip("Number of CPU cores for running Solidity")

        self._input_group = QWidget()
        layout_cpu_controls.addWidget(self._cpu_label)
        layout_cpu_controls.addWidget(self._cpu_spin_box)
        self._input_group.setLayout(layout_cpu_controls)
        layout.addWidget(self._input_group)

    def _toggle_sweep_controls(self, checked: bool) -> None:
        self._input_group.setEnabled(not checked)
        self._start_btn.setEnabled(checked)

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

    def sweep_and_generate_output(
        self, elastic_property: Property, value: int, dir_path: str
    ) -> None:
        """Set the material property sweep value and generate output files."""
        if elastic_property.data is None:
            elastic_property.data = {}
        if not elastic_property.data["poissons_ratio"]:
            elastic_property.data["poissons_ratio"] = elastic_property.default_data[
                "poissons_ratio"
            ]
        elastic_property.data["youngs_modulus"] = value
        lame_lambda, lame_mu = calculate_lame_constants(
            cast(float, elastic_property.data["youngs_modulus"]),
            cast(float, elastic_property.data["poissons_ratio"]),
        )
        elastic_property.data["lame_lambda"] = lame_lambda
        elastic_property.data["lame_mu"] = lame_mu
        output_dir = Path(dir_path) / f"{value:.3e}"
        output_dir.mkdir(parents=True, exist_ok=True)
        generate_output_files(output_dir=output_dir)
        if self.layout_file_path and self.pellet_file_path:
            shutil.copy(self.layout_file_path, output_dir / "layout.txt")
            shutil.copy(self.pellet_file_path, output_dir / "pellet.txt")

    def _start_solidity(self) -> None:
        if self._sweep_group.isChecked():
            self._log("Parameter sweep mode is enabled")
            dir_path = QFileDialog.getExistingDirectory(
                self, "Select output directory for parameter sweep"
            )
            if not dir_path:
                self._log("Parameter sweep cancelled.")
                return
            material_key = self._sweep_material_combo.currentData()
            start = self._sweep_start.value()
            stop = self._sweep_stop.value()
            step = self._sweep_step.value()
            sweep_values = [
                start + i * step for i in range(int((stop - start) / step) + 1)
            ]
            elastic_property = material_datastore[material_key].properties["elasticity"]

            sweep_dirs = []
            self._job_list_widget.clear()
            self._job_outputs: dict[Path, dict] = {}  # sweep_dir -> result dict
            for value in sweep_values:
                self._log(f"Sweeping Young's modulus: {value:.3e}")
                self.sweep_and_generate_output(elastic_property, value, dir_path)
                sweep_dir = Path(dir_path) / f"{value:.3e}"
                sweep_dirs.append(sweep_dir)
                self._job_list_widget.addItem(str(sweep_dir))

            self._progress_bar.setMaximum(len(sweep_dirs))
            self._progress_bar.setValue(0)

            total_cpus = cpu_count() or 1
            num_jobs = len(sweep_dirs)
            if num_jobs <= total_cpus:
                num_cpus = max(1, total_cpus // num_jobs)
                max_workers = num_jobs
            else:
                num_cpus = 1
                max_workers = total_cpus
            self._log(
                f"Running {num_jobs} jobs in parallel "
                f"(max_workers={max_workers}, {num_cpus} CPUs per job, "
                f"{total_cpus} CPUs available)"
            )

            def job_done_callback(future: concurrent.futures.Future) -> None:
                """Log the result of a completed future and update progress."""
                result = future.result()
                self.job_done_signal.emit(result)

            executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

            futures = [
                executor.submit(self._run_solidity_job, sweep_dir, num_cpus)
                for sweep_dir in sweep_dirs
            ]
            for future in futures:
                future.add_done_callback(job_done_callback)
        else:
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

    def _run_solidity_job(self, sweep_dir: Path, num_cpus: int) -> dict:
        """Run the Solidity solver for a given sweep directory."""
        try:
            y3d_file = sweep_dir / "BST.Y3D"
            mat_file = sweep_dir / "mat.txt"
            layout_file = sweep_dir / "layout.txt"
            pellet_file = sweep_dir / "pellet.txt"
            # Check all files exist
            for f in [y3d_file, mat_file, layout_file, pellet_file]:
                if not f.exists():
                    return {
                        "sweep_dir": str(sweep_dir),
                        "status": "error",
                        "error": f"Missing file: {f.name}",
                    }
            from solidity_gui.solidity import run_solidity_no_stream

            container_name = f"solidity_{sweep_dir.name.replace('+', '_')}"

            container = run_solidity_no_stream(
                y3d_file_path=y3d_file,
                layout_file_path=layout_file,
                pellet_file_path=pellet_file,
                materials_file_path=mat_file,
                num_cpus=num_cpus,
                container_name=container_name,
            )

            # We need to wait for the container to finish before returning from the job
            exit_code = docker.container.wait(container_name)
            # And then clean up the container
            container.remove()
            return {
                "sweep_dir": str(sweep_dir),
                "status": "success",
                "container_id": str(container.id),
                "exit_code": exit_code,
            }
        except Exception as e:
            return {"sweep_dir": str(sweep_dir), "status": "error", "error": str(e)}

    def _on_job_done(self, result: dict) -> None:
        """Handle a completed job."""
        sweep_dir = Path(result["sweep_dir"])
        self._job_outputs[sweep_dir] = result
        completed_jobs = len(self._job_outputs)
        self._progress_bar.setValue(completed_jobs)
        if result["status"] == "success":
            self._log(f"Completed {sweep_dir}")
        else:
            self._log(f"Error in {sweep_dir}: {result['error']}")
        if completed_jobs == self._progress_bar.maximum():
            self._log("All jobs completed.")
            self._start_btn.setEnabled(True)
            self._stop_btn.setEnabled(False)
            self._cpu_spin_box.setEnabled(True)


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
