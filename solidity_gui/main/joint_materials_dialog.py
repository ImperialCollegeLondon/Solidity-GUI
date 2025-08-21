"""Module for JointMaterialsDialog class."""

from typing import Any

from pubsub import pub
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .gmsh_process import gmsh_process_datastore
from .joint_materials_form import JointMaterialFormDialog
from .material import (
    get_joint_material_interfaces,
    joint_material_datastore,
    material_assignment_datastore,
    material_datastore,
)


class JointMaterialsDialog(QDialog):
    """Dialog for managing parameters for joint elements between materials."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create a new JointMaterialsDialog."""
        super().__init__(*args, **kwargs)
        layout = QVBoxLayout(self)

        joint_material_interfaces = get_joint_material_interfaces(
            gmsh_process_datastore, material_assignment_datastore
        )

        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            ["Material 1", "Material 2", "Parameters Set?"]
        )
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for mat1, mat2 in joint_material_interfaces:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(mat1.name))
            self.table.setItem(row, 1, QTableWidgetItem(mat2.name))

        self._update_parameters_set_column()

        add_button = QPushButton("Edit parameters")
        add_button.clicked.connect(self._edit_clicked)
        layout.addWidget(add_button)

        pub.subscribe(self._clear_assignments, "session.new")

    def _clear_assignments(self) -> None:
        self.table.setRowCount(0)

    def _update_parameters_set_column(self) -> None:
        for i in range(self.table.rowCount()):
            _, material1 = material_datastore.get_by_name(self.table.item(i, 0).text())
            _, material2 = material_datastore.get_by_name(self.table.item(i, 1).text())
            try:
                joint_material_datastore.get_by_materials(material1, material2)
            except ValueError:
                self.table.setItem(i, 2, QTableWidgetItem("no"))
            else:
                self.table.setItem(i, 2, QTableWidgetItem("yes"))

    def _edit_clicked(self) -> None:
        if self.table.selectedIndexes():
            row = self.table.currentRow()
            _, material1 = material_datastore.get_by_name(
                self.table.item(row, 0).text()
            )
            _, material2 = material_datastore.get_by_name(
                self.table.item(row, 1).text()
            )
            JointMaterialFormDialog((material1, material2)).exec()
            self._update_parameters_set_column()
