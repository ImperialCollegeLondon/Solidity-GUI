"""Module for the AssignInitialConditionsDialog class."""
import logging
from operator import attrgetter

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .assignment_table import AssignmentTable
from .initial_condition import (
    InitialConditionAssignment,
    initial_condition_assignment_datastore,
    initial_condition_datastore,
)
from .mesh_selection_combobox import MeshSelectionComboBox
from .meshes import mesh_datastore


class AssignInitialConditionsDialog(QDialog):
    """Dialog for assigning conditions to geometries."""

    def __init__(self) -> None:
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle("Assign Initial Conditions")

        layout = QVBoxLayout(self)

        self.select_component_combo = MeshSelectionComboBox()
        self.select_condition_combo = QComboBox()

        self.select_component_combo.setSizeAdjustPolicy(
            QComboBox.AdjustToContents  # type: ignore[attr-defined]
        )
        self.select_condition_combo.setSizeAdjustPolicy(
            QComboBox.AdjustToContents  # type: ignore[attr-defined]
        )

        layout.addWidget(QLabel("Component:"))
        layout.addWidget(self.select_component_combo)
        layout.addWidget(QLabel("Condition:"))
        layout.addWidget(self.select_condition_combo)

        self._populate_combos()

        add_button = QPushButton("Add")
        add_button.clicked.connect(self._add_clicked)
        layout.addWidget(add_button)

        layout.addWidget(QLabel("Initial Condition Assignments:"))

        self.table = AssignmentTable(
            ["Initial Condition"], [attrgetter("initial_condition.name")]
        )

        layout.addWidget(self.table)

        self.table.add_items(initial_condition_assignment_datastore.values())

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
                    for assignment in initial_condition_assignment_datastore.values()
                ]
            ]
        )
        for key, condition in initial_condition_datastore.items():
            self.select_condition_combo.addItem(condition.name, userData=key)

    def _add_clicked(self) -> None:
        selected_component_value = self.select_component_combo.currentText()
        selected_condition_value = self.select_condition_combo.currentData()
        if not selected_component_value or selected_condition_value is None:
            return
        condition = initial_condition_datastore[selected_condition_value]
        assignment = InitialConditionAssignment(
            initial_condition=condition,
            cell_set_name=selected_component_value,
        )
        initial_condition_assignment_datastore.add(assignment)

        self.table.add_items([assignment])

        self._populate_combos()

        logging.info(
            f"Assigned condition {condition.name} to {assignment.cell_set_name}"
        )

    def _remove_clicked(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        for row in selected_rows:
            for index in initial_condition_assignment_datastore:
                assignment = initial_condition_assignment_datastore[index]
                if (
                    assignment.cell_set_name == self.table.item(row.row(), 0).text()
                    and assignment.initial_condition.name
                    == self.table.item(row.row(), 1).text()
                ):
                    del initial_condition_assignment_datastore[index]
                    self.table.removeRow(row.row())

                    logging.info(
                        "Removed initial condition assignment "
                        f"{assignment.initial_condition.name} to "
                        f"{assignment.cell_set_name}"
                    )

                    break

        self._populate_combos()
