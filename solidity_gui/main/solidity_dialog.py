"""This module provides functionality to run Solidity."""

import concurrent.futures
import html
import logging
import shutil
import threading
import weakref
from collections.abc import Callable, Iterable
from contextlib import suppress
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
from .forms.widgets import LargeFloatLineWidget
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


def compute_worker_assignment(num_jobs: int) -> tuple[int, int, int]:
    """Compute the number of CPUs per job and max workers for the executor."""
    total_cpus = cpu_count() or 1
    if num_jobs <= total_cpus:
        num_cpus = max(1, total_cpus // num_jobs)
        max_workers = num_jobs
    else:
        num_cpus = 1
        max_workers = total_cpus
    return num_cpus, max_workers, total_cpus


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

        self._executor: concurrent.futures.ThreadPoolExecutor | None = None
        self._futures: list[concurrent.futures.Future] = []
        self._job_outputs: dict[Path, dict] = {}
        # Track sweep dirs for running jobs so we can stop their containers
        self._sweep_dirs: list[Path] = []

        # self._setup_cpu_ui(layout)
        self._setup_mode_tabs(layout)

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

        self._update_mode_ui()

        pub.subscribe(self._on_docker_pulled, "docker.pulled")
        pub.subscribe(self._on_docker_started, "docker.started")
        pub.subscribe(self._on_docker_stopped, "docker.stopped")
        pub.subscribe(self._on_docker_error, "docker.error")
        pub.subscribe(self._log, "docker.output")
        self.job_done_signal.connect(self._on_job_done)

        self._logger = self._create_logger()
        self.log_updated.connect(self._update_log_text_edit)

    def _set_running_ui(self, running: bool) -> None:
        """Set the UI state for running or stopped."""
        self._start_btn.setEnabled(not running)
        self._stop_btn.setEnabled(running)
        self._cpu_spin_box.setEnabled(not running)

    def _shutdown_executor(self, cancel_futures: bool) -> None:
        """Shut down the executor and cancel any running futures."""
        if self._executor is not None:
            self._log("Shutting down executor...")
            # If cancelling futures, also stop their containers
            if cancel_futures and self._sweep_dirs:
                for sweep_dir in self._sweep_dirs:
                    container_name = f"solidity_{sweep_dir.name.replace('+', '_')}"
                    with suppress(DockerException):
                        docker.container.stop(container_name)
                # Clear tracked dirs immediately
                self._sweep_dirs.clear()
            if cancel_futures:
                for f in self._futures:
                    with suppress(Exception):
                        f.cancel()
            with suppress(Exception):
                self._executor.shutdown(wait=False, cancel_futures=cancel_futures)
            self._executor = None
            self._futures.clear()

    def _make_done_callback(
        self, sweep_dir: Path
    ) -> Callable[[concurrent.futures.Future], None]:
        """Return a done-callback that emits a result dict."""

        def job_done_callback(future: concurrent.futures.Future) -> None:
            if future.cancelled():
                result = {
                    "sweep_dir": str(sweep_dir),
                    "status": "cancelled",
                    "error": "job cancelled",
                }
            else:
                try:
                    result = future.result()
                    result.setdefault("sweep_dir", str(sweep_dir))
                except Exception as e:
                    result = {
                        "sweep_dir": str(sweep_dir),
                        "status": "error",
                        "error": str(e),
                    }
            self.job_done_signal.emit(result)

        return job_done_callback

    def _select_input_files(self) -> None:
        """Select input files for Solidity."""
        file_paths = get_file_paths()
        if file_paths:
            self.y3d_file_path = file_paths[0]
            self.layout_file_path = file_paths[2]
            self.pellet_file_path = file_paths[3]
            self.materials_file_path = file_paths[1]
            self._update_mode_ui()
            self._log("Input files selected.")
        else:
            self._log("File selection cancelled or incomplete.")

    def _setup_parameter_sweep_ui(self, layout: QVBoxLayout) -> None:
        """Set up the UI elements for parameter sweep using a QGroupBox."""
        from PySide6.QtWidgets import QGroupBox

        self._sweep_group = QGroupBox("Parameter Sweep (Young's Modulus)")
        self._sweep_group.setToolTip(
            "Enable this option to run a parameter sweep over Young's modulus. "
            "All sweep controls will be enabled, and input file selection will be "
            "disabled."
        )
        sweep_layout = QVBoxLayout()

        self._sweep_material_combo = QComboBox()

        start_widget = LargeFloatLineWidget()
        stop_widget = LargeFloatLineWidget()
        step_widget = LargeFloatLineWidget()

        self._sweep_start = start_widget.create(None, [])
        self._sweep_stop = stop_widget.create(None, [])
        self._sweep_step = step_widget.create(None, [])

        self._sweep_start.setPlaceholderText("Start (e.g. 1.23E+04)")
        self._sweep_stop.setPlaceholderText("Stop (e.g. 1.00E+18)")
        self._sweep_step.setPlaceholderText("Step (e.g. 1.23E+03)")

        self._populate_sweep_material_combo()
        self._sweep_material_combo.currentIndexChanged.connect(
            self._update_sweep_values
        )

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

        # LargeFloatLineWidget does not support a prefix text, so let's use labels
        start_col = QVBoxLayout()
        start_col.addWidget(QLabel("Start:"))
        start_col.addWidget(self._sweep_start)
        param_values_layout.addLayout(start_col)

        stop_col = QVBoxLayout()
        stop_col.addWidget(QLabel("Stop:"))
        stop_col.addWidget(self._sweep_stop)
        param_values_layout.addLayout(stop_col)

        step_col = QVBoxLayout()
        step_col.addWidget(QLabel("Step:"))
        step_col.addWidget(self._sweep_step)
        param_values_layout.addLayout(step_col)

        sweep_layout.addLayout(param_values_layout)
        self._sweep_group.setLayout(sweep_layout)
        layout.addWidget(self._sweep_group)

    def _setup_mode_tabs(self, parent_layout: QVBoxLayout) -> None:
        """Create QTabWidget and populate three pages (Single, Batch, Sweep)."""
        from PySide6.QtWidgets import QTabWidget

        self._mode_tabs = QTabWidget()

        # Single Run tab
        single = QWidget()
        single_layout = QVBoxLayout()
        self._setup_cpu_ui(single_layout)
        single.setLayout(single_layout)
        self._mode_tabs.addTab(single, "Single Run")

        # Batch Run tab
        batch = QWidget()
        batch_layout = QVBoxLayout()
        batch_row = QHBoxLayout()
        self._batch_dir_btn = QPushButton("Select Batch Run Directory")
        self._batch_dir_btn.clicked.connect(self._select_batch_parent_dir)
        self._batch_dir_label = QLabel("No directory selected")
        self._batch_parent_dir: Path | None = None
        batch_row.addWidget(self._batch_dir_btn)
        batch_row.addWidget(self._batch_dir_label)
        batch_layout.addLayout(batch_row)
        batch.setLayout(batch_layout)
        self._mode_tabs.addTab(batch, "Batch Run")

        # Parameter Sweep tab
        sweep = QWidget()
        sweep_layout = QVBoxLayout()
        self._setup_parameter_sweep_ui(sweep_layout)
        sweep.setLayout(sweep_layout)
        self._mode_tabs.addTab(sweep, "Parameter Sweep")

        parent_layout.addWidget(self._mode_tabs)
        self._mode_tabs.currentChanged.connect(self._update_mode_ui)

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
        cpus = cpu_count() or 1
        self._cpu_spin_box.setRange(1, cpus)
        self._cpu_spin_box.setValue(cpus)
        self._cpu_spin_box.setToolTip("Number of CPU cores for running Solidity")

        self._input_group = QWidget()
        layout_cpu_controls.addWidget(self._cpu_label)
        layout_cpu_controls.addWidget(self._cpu_spin_box)
        self._input_group.setLayout(layout_cpu_controls)
        layout.addWidget(self._input_group)

    def _select_batch_parent_dir(self) -> None:
        """Select the parent directory for batch run."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Batch Run Parent Directory"
        )
        if dir_path:
            self._batch_parent_dir = Path(dir_path)
            self._batch_dir_label.setText(str(dir_path))
        else:
            self._batch_parent_dir = None
            self._batch_dir_label.setText("No directory selected")

        self._update_mode_ui()

    def _update_mode_ui(self) -> None:
        """Update minimal runtime UI state (Start button) based on active tab."""
        idx = self._mode_tabs.currentIndex()

        have_inputs = all(
            [
                self.y3d_file_path,
                self.layout_file_path,
                self.pellet_file_path,
                self.materials_file_path,
            ]
        )

        if idx == 0:  # Single Run
            self._start_btn.setEnabled(have_inputs)
        elif idx == 1:  # Batch Run
            self._start_btn.setEnabled(self._batch_parent_dir is not None)
        else:  # Parameter Sweep
            self._start_btn.setEnabled(have_inputs)

    def _populate_sweep_material_combo(self) -> None:
        self._sweep_material_combo.clear()
        for key, material in material_datastore.items():
            if material.properties["elasticity"].enabled:
                self._sweep_material_combo.addItem(material.name, userData=key)

        self._update_sweep_values()

    def _update_sweep_values(self) -> None:
        material_name = self._sweep_material_combo.currentData()
        if material_name is None:
            self._sweep_start.setText("0.0")
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
        self._sweep_start.setText(f"{youngs_modulus:E}")
        self._sweep_stop.setText(f"{1e18:E}")
        self._sweep_step.setText(
            f"{youngs_modulus / 10 if youngs_modulus > 0 else 1.0:E}"
        )

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
        self, elastic_property: Property, value: float, dir_path: str
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

    def _sweep_then_run(
        self, elastic_property: Property, value: float, dir_path: str, num_cpus: int
    ) -> dict:
        """Worker wrapper: create output files for one sweep value, then run the job."""
        try:
            # generate files (runs on worker thread)
            self.sweep_and_generate_output(elastic_property, value, dir_path)
            sweep_dir = Path(dir_path) / f"{value:.3e}"
            return self._run_solidity_job(sweep_dir, num_cpus)
        except Exception as e:
            return {
                "sweep_dir": str(Path(dir_path) / f"{value:.3e}"),
                "status": "error",
                "error": str(e),
            }

    def _prepare_and_start_parallel(self, dirs: list[Path], mode_label: str) -> int:
        """Shared prep for batch / sweep."""
        # Reset outputs from any previous runs so progress counting is accurate
        self._job_outputs.clear()
        self._job_list_widget.clear()
        self._progress_bar.setValue(0)

        for sweep_dir in dirs:
            self._job_list_widget.addItem(str(sweep_dir))
        self._progress_bar.setMaximum(len(dirs))
        self._progress_bar.setValue(0)

        num_jobs = len(dirs)
        num_cpus, max_workers, total_cpus = compute_worker_assignment(num_jobs)
        self._log(
            f"Running {num_jobs} jobs in parallel "
            f"(max_workers={max_workers}, {num_cpus} CPUs per job, "
            f"{total_cpus} CPUs available) ({mode_label})"
        )

        # Immediately update UI
        self._set_running_ui(True)
        self._log(f"Scheduling {mode_label.lower()} jobs...")

        # Cancel any previous run before starting a new one
        self._shutdown_executor(cancel_futures=True)

        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        # remember sweep dirs for shutdown logic
        self._sweep_dirs = list(dirs)
        return num_cpus

    def _start_solidity_sweep(self) -> None:
        self._log("Parameter sweep mode is enabled")
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select output directory for parameter sweep"
        )
        if not dir_path:
            self._log("Parameter sweep cancelled.")
            return
        material_key = self._sweep_material_combo.currentData()
        if material_key is None:
            display_error_message("Please select a material for the sweep.")
            return
        try:
            start = float(self._sweep_start.text())
            stop = float(self._sweep_stop.text())
            step = float(self._sweep_step.text())
        except ValueError:
            display_error_message("Please enter valid numeric values for the sweep.")
            return
        if step <= 0 or stop < start:
            display_error_message(
                "Please ensure that Stop > Start and Step > 0 for the sweep."
            )
            return
        sweep_values = [start + i * step for i in range(int((stop - start) / step) + 1)]
        elastic_property = material_datastore[material_key].properties["elasticity"]

        sweep_dirs: list[Path] = [
            Path(dir_path) / f"{value:.3e}" for value in sweep_values
        ]

        num_cpus = self._prepare_and_start_parallel(sweep_dirs, "Parameter Sweep")

        # Submit tasks that first generate outputs then run the container
        # This keeps the file creation off the UI thread
        for v in sweep_values:
            sweep_dir = Path(dir_path) / f"{v:.3e}"
            executor = self._executor
            assert executor is not None
            future = executor.submit(
                self._sweep_then_run, elastic_property, v, dir_path, num_cpus
            )
            future.add_done_callback(self._make_done_callback(sweep_dir))
            self._futures.append(future)

    def _start_solidity_batch(self) -> None:
        # Batch Run: use existing sub-directories under a chosen parent directory
        if not self._batch_parent_dir:
            display_error_message("Please select a batch run directory first.")
            return

        parent = Path(self._batch_parent_dir)
        subdirs = sorted([p for p in parent.iterdir() if p.is_dir()])
        if not subdirs:
            display_error_message(
                "No sub-directories found in the selected batch run directory."
            )
            return

        num_cpus = self._prepare_and_start_parallel(subdirs, "Batch Run")

        # Submit tasks: run solver in each subdir
        for sd in subdirs:
            executor = self._executor
            assert executor is not None
            future = executor.submit(self._run_solidity_job, sd, num_cpus)
            future.add_done_callback(self._make_done_callback(sd))
            self._futures.append(future)

    def _start_solidity_single(self) -> None:
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

    def _start_solidity(self) -> None:
        tab = self._mode_tabs.currentIndex()
        if tab == 2:
            self._start_solidity_sweep()
        elif tab == 1:
            self._start_solidity_batch()
        elif tab == 0:
            self._start_solidity_single()

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
        # Stop button pressed — update UI immediately and perform shutdown in background
        self._stop_btn.setEnabled(False)
        self._log("==========\nStop requested — cancelling jobs...")
        # Flip UI immediately so user sees the state change
        self._set_running_ui(False)
        # Broadcast docker stop so in-job docker waits can return
        pub.sendMessage("docker.stop")
        # Perform cancel/stop/shutdown asynchronously to avoid blocking UI
        threading.Thread(
            target=lambda: self._shutdown_executor(cancel_futures=True), daemon=True
        ).start()
        self._log("Stop requested — shutdown running in background.")

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
            wait_result = docker.container.wait(container_name)
            # python-on-whales may return {'StatusCode': int} or an int
            if isinstance(wait_result, dict):
                exit_code = wait_result.get("StatusCode", -1)
            else:
                exit_code = int(wait_result)
            with suppress(DockerException, Exception):
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
        sweep_dir = Path(result.get("sweep_dir", "<unknown>"))
        self._job_outputs[sweep_dir] = result
        # Remove from tracked dirs since it's done
        with suppress(ValueError):
            if sweep_dir in self._sweep_dirs:
                self._sweep_dirs.remove(sweep_dir)
        completed_jobs = len(self._job_outputs)
        self._progress_bar.setValue(completed_jobs)
        if result["status"] == "success":
            self._log(f"Completed {sweep_dir}")
        else:
            self._log(f"Error in {sweep_dir}: {result['error']}")
        if completed_jobs == self._progress_bar.maximum():
            self._log("All jobs completed.")

            # Only teardown executor if we actually have one and all futures are done
            if self._executor is not None and all(f.done() for f in self._futures):
                self._shutdown_executor(cancel_futures=False)
            self._set_running_ui(False)


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
