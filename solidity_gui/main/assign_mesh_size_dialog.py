"""Module for the AssignMeshSizeDialog class."""

import logging
from operator import attrgetter

from pubsub import pub
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .assignment_table import AssignmentTable
from .mesh_selection_combobox import MeshSelectionComboBox
from .mesh_sizes import MeshSize, mesh_size_datastore
from .meshes import mesh_datastore


class AssignMeshSizeDialog(QDialog):
    """Dialog for assigning mesh sizes to geometries."""

    def __init__(self) -> None:
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle("Assign Mesh Sizes")

        layout = QVBoxLayout(self)

        self.component_combo = MeshSelectionComboBox()
        self.mesh_size_spinbox = QDoubleSpinBox()
        self.mesh_size_spinbox.setValue(0.1)
        self.mesh_size_spinbox.setDecimals(4)
        self.mesh_size_spinbox.setMinimum(0.0001)

        self.component_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )

        layout.addWidget(QLabel("Component:"))
        layout.addWidget(self.component_combo)
        layout.addWidget(QLabel("Mesh Size:"))
        layout.addWidget(self.mesh_size_spinbox)

        self._populate_combo()

        add_button = QPushButton("Add")
        add_button.clicked.connect(self._add_clicked)
        layout.addWidget(add_button)

        layout.addWidget(QLabel("Assignments:"))

        self.table = AssignmentTable(
            ["Mesh Size"],
            [attrgetter("size")],
        )

        layout.addWidget(self.table)

        self.table.add_items(mesh_size_datastore.values())

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self._remove_clicked)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        button_layout = QHBoxLayout()
        button_layout.addWidget(remove_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        pub.subscribe(self._clear_assignments, "session.new")

    def _clear_assignments(self) -> None:
        self.table.setRowCount(0)

    def _populate_combo(self) -> None:
        self.component_combo.clear()

        assigned_cell_sets = [
            mesh_size.cell_set_name for mesh_size in mesh_size_datastore.values()
        ]
        self.component_combo.addItems(
            [
                key
                for mesh in mesh_datastore.values()
                for key in mesh.cell_sets.keys()
                if key not in assigned_cell_sets
            ]
        )

    def _add_clicked(self) -> None:
        selected_component_value = self.component_combo.currentText()
        if not selected_component_value:
            return

        mesh_size = MeshSize(
            cell_set_name=selected_component_value, size=self.mesh_size_spinbox.value()
        )
        mesh_size_datastore.add(mesh_size)

        self.table.add_items([mesh_size])
        self._populate_combo()

        logging.info(
            f"Assigned mesh size {mesh_size.size} to {mesh_size.cell_set_name}"
        )

    def _remove_clicked(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        for row in selected_rows:
            for index, mesh_size in mesh_size_datastore.items():
                if mesh_size.cell_set_name == self.table.item(row.row(), 0).text():
                    del mesh_size_datastore[index]
                    self.table.removeRow(row.row())

                    logging.info(
                        f"Removed mesh size {mesh_size.size} from "
                        f"{mesh_size.cell_set_name}"
                    )

                    break

        self._populate_combo()
