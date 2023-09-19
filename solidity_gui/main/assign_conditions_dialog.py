"""Module for the AssignConditionsDialog class."""
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

from .condition import (
    ConditionAssignment,
    condition_assignment_datastore,
    condition_datastore,
)
from .mesh_selection_combobox import MeshSelectionComboBox
from .meshes import mesh_datastore


class AssignConditionsDialog(QDialog):
    """Dialog for assigning conditions to geometries."""

    def __init__(self) -> None:
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle("Assign Conditions")

        layout = QVBoxLayout(self)

        self.select_component_combo = MeshSelectionComboBox()
        self.select_condition_combo = QComboBox()

        self.select_component_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.select_condition_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        layout.addWidget(QLabel("Component:"))
        layout.addWidget(self.select_component_combo)
        layout.addWidget(QLabel("Condition:"))
        layout.addWidget(self.select_condition_combo)

        self._populate_combos()

        add_button = QPushButton("Add")
        add_button.clicked.connect(self._add_clicked)
        layout.addWidget(add_button)

        layout.addWidget(QLabel("Condition Assignments:"))

        self.condition_assignment_table = QTableWidget()
        self.condition_assignment_table.setColumnCount(2)
        self.condition_assignment_table.setHorizontalHeaderLabels(
            ["Component", "Condition"]
        )
        self.condition_assignment_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.condition_assignment_table.horizontalHeader().setHighlightSections(False)
        self.condition_assignment_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.condition_assignment_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.condition_assignment_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        layout.addWidget(self.condition_assignment_table)

        for assignment in condition_assignment_datastore.values():
            row = self.condition_assignment_table.rowCount()
            self.condition_assignment_table.insertRow(row)
            self.condition_assignment_table.setItem(
                row, 0, QTableWidgetItem(assignment.cell_set_name)
            )
            self.condition_assignment_table.setItem(
                row, 1, QTableWidgetItem(assignment.condition.name)
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
        self.select_condition_combo.clear()

        self.select_component_combo.addItems(
            [
                key
                for mesh in mesh_datastore.values()
                for key, value in mesh.cell_sets.items()
                if key
                not in [
                    assignment.cell_set_name
                    for assignment in condition_assignment_datastore.values()
                ]
            ]
        )
        for key, condition in condition_datastore.items():
            self.select_condition_combo.addItem(condition.name, userData=key)

    def _add_clicked(self) -> None:
        selected_component_value = self.select_component_combo.currentText()
        selected_condition_value = self.select_condition_combo.currentData()
        if not selected_component_value or selected_condition_value is None:
            return
        condition = condition_datastore[selected_condition_value]
        assignment = ConditionAssignment(
            condition=condition,
            cell_set_name=selected_component_value,
        )
        condition_assignment_datastore.add(assignment)

        row = self.condition_assignment_table.rowCount()
        self.condition_assignment_table.insertRow(row)
        self.condition_assignment_table.setItem(
            row, 0, QTableWidgetItem(assignment.cell_set_name)
        )
        self.condition_assignment_table.setItem(
            row, 1, QTableWidgetItem(assignment.condition.name)
        )

        self._populate_combos()

        logging.info(
            f"Assigned condition {condition.name} to {assignment.cell_set_name}"
        )

    def _remove_clicked(self) -> None:
        selected_rows = self.condition_assignment_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        for row in selected_rows:
            for index in condition_assignment_datastore:
                assignment = condition_assignment_datastore[index]
                if (
                    assignment.cell_set_name
                    == self.condition_assignment_table.item(row.row(), 0).text()
                    and assignment.condition.name
                    == self.condition_assignment_table.item(row.row(), 1).text()
                ):
                    del condition_assignment_datastore[index]
                    self.condition_assignment_table.removeRow(row.row())

                    logging.info(
                        f"Removed condition assignment {assignment.condition.name} to "
                        f"{assignment.cell_set_name}"
                    )

                    break

        self._populate_combos()
