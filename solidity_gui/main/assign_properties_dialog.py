"""Module for the AssignPropertiesDialog class."""

import logging
from operator import attrgetter

from pubsub import pub
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .assignment_table import AssignmentTable
from .material import (
    MaterialAssignment,
    material_assignment_datastore,
    material_datastore,
)
from .mesh_selection_combobox import MeshSelectionComboBox
from .meshes import mesh_datastore


class AssignPropertiesDialog(QDialog):
    """Dialog for assigning properties to geometries."""

    def __init__(self) -> None:
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle("Assign Properties")

        layout = QVBoxLayout(self)

        self.select_component_combo = MeshSelectionComboBox()
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

        self.material_assignment_table = AssignmentTable(
            ["Material"],
            [attrgetter("material.name")],
        )

        layout.addWidget(self.material_assignment_table)

        self.material_assignment_table.add_items(material_assignment_datastore.values())

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
        self.material_assignment_table.setRowCount(0)

    def _populate_combos(self) -> None:
        self.select_component_combo.clear()
        self.select_material_combo.clear()

        self.select_component_combo.addItems(
            [
                key
                for mesh in mesh_datastore.values()
                for key in mesh.cell_sets.keys()
                if "volume" in key
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

        self.material_assignment_table.add_items([assignment])
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
