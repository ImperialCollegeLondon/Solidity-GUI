"""Module for the AssignPropertiesDialog class."""
import logging

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .material import (
    MaterialAssignment,
    material_assignment_datastore,
    material_datastore,
)
from .meshes import mesh_datastore


class AssignPropertiesDialog(QDialog):
    """Dialog for assigning properties to geometries."""

    def __init__(self) -> None:
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle("Assign Properties")

        layout = QVBoxLayout(self)

        self.select_component_combo = QComboBox()
        self.select_material_combo = QComboBox()

        self.select_component_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.select_material_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        layout.addWidget(QLabel("Component:"))
        layout.addWidget(self.select_component_combo)
        layout.addWidget(QLabel("Material:"))
        layout.addWidget(self.select_material_combo)

        self._populate_combos()

        add_button = QPushButton("Add")
        add_button.clicked.connect(self._add_clicked)
        layout.addWidget(add_button)

        layout.addWidget(QLabel("Material Assignments:"))

        self.material_assignment_table = QTableWidget()
        self.material_assignment_table.setColumnCount(2)
        self.material_assignment_table.setHorizontalHeaderLabels(
            ["Component", "Material"]
        )
        self.material_assignment_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.material_assignment_table.horizontalHeader().setHighlightSections(False)
        self.material_assignment_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.material_assignment_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.material_assignment_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        layout.addWidget(self.material_assignment_table)

        for assignment in material_assignment_datastore.values():
            row = self.material_assignment_table.rowCount()
            self.material_assignment_table.insertRow(row)
            self.material_assignment_table.setItem(
                row, 0, QTableWidgetItem(assignment.cell_set_name)
            )
            self.material_assignment_table.setItem(
                row, 1, QTableWidgetItem(assignment.material.name)
            )

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self._remove_clicked)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        button_layout = QHBoxLayout()
        button_layout.addWidget(remove_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def _populate_combos(self) -> None:
        self.select_component_combo.clear()
        self.select_material_combo.clear()

        self.select_component_combo.addItems(
            [
                key
                for mesh in mesh_datastore.values()
                for key, value in mesh.cell_sets.items()
                if value[2] is not None
                and key
                not in [
                    assignment.cell_set_name
                    for assignment in material_assignment_datastore.values()
                ]
            ]
        )
        for key, material in material_datastore.items():
            self.select_material_combo.addItem(material.name, userData=key)

    def _add_clicked(self) -> None:
        selected_component_value = self.select_component_combo.currentText()
        selected_material_value = self.select_material_combo.currentData()
        if not selected_component_value or selected_material_value is None:
            return
        material = material_datastore[selected_material_value]
        assignment = MaterialAssignment(
            material=material,
            cell_set_name=selected_component_value,
        )
        material_assignment_datastore.add(assignment)

        row = self.material_assignment_table.rowCount()
        self.material_assignment_table.insertRow(row)
        self.material_assignment_table.setItem(
            row, 0, QTableWidgetItem(assignment.cell_set_name)
        )
        self.material_assignment_table.setItem(
            row, 1, QTableWidgetItem(assignment.material.name)
        )

        self._populate_combos()

        logging.info(f"Assigned material {material.name} to {assignment.cell_set_name}")

    def _remove_clicked(self) -> None:
        selected_rows = self.material_assignment_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        for row in selected_rows:
            for index in material_assignment_datastore:
                assignment = material_assignment_datastore[index]
                if (
                    assignment.cell_set_name
                    == self.material_assignment_table.item(row.row(), 0).text()
                    and assignment.material.name
                    == self.material_assignment_table.item(row.row(), 1).text()
                ):
                    del material_assignment_datastore[index]
                    self.material_assignment_table.removeRow(row.row())

                    logging.info(
                        f"Removed material assignment {assignment.material.name} to "
                        f"{assignment.cell_set_name}"
                    )

                    break

        self._populate_combos()
