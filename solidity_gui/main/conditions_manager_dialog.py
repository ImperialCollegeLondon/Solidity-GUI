"""Module for the MaterialsManagerDialog class."""
import logging
from copy import deepcopy

from pubsub import pub
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .edit_material_dialog import EditMaterialDialog
from .material import Material, material_datastore


class ConditionsManagerDialog(QDialog):
    """Dialog for managing conditions.

    Conditions can be created from this dialog.
    Created Conditions will be shown in the tree view in this dialog.
    """

    def __init__(self) -> None:
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle("Conditions Manager")
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.conditions_table = QTableWidget()
        # allow user to only select one row
        self.conditions_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.conditions_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # disable editing of table items
        self.conditions_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.conditions_table.setColumnCount(2)
        self.conditions_table.setHorizontalHeaderLabels(["Name", "ID"])
        # by default, QTableWidgets display a row index
        # we can disable this since we are manually setting an ID later
        self.conditions_table.verticalHeader().setVisible(False)
        # distribute the available space according to the
        # space requirement of each column
        header = self.conditions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        layout.addWidget(self.conditions_table)

        self.create_button = QPushButton("Create")
        self.edit_button = QPushButton("Edit")
        self.rename_button = QPushButton("Rename")
        self.copy_button = QPushButton("Copy")
        self.delete_button = QPushButton("Delete")

        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.create_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.rename_button)
        buttons_layout.addWidget(self.copy_button)
        buttons_layout.addWidget(self.delete_button)

        layout.addLayout(buttons_layout)

        self.create_button.clicked.connect(self._create_click_handler)
        self.edit_button.clicked.connect(self._edit_click_handler)
        self.rename_button.clicked.connect(self._rename_click_handler)
        self.copy_button.clicked.connect(self._copy_click_handler)
        self.delete_button.clicked.connect(self._delete_click_handler)

        self.conditions_table.cellChanged.connect(self._material_renamed)

        pub.subscribe(self._add_material, material_datastore.update_topic)

    def _create_click_handler(self) -> None:
        pass
        # CreateConditionsDialog(material_datastore).exec()

    def _edit_click_handler(self) -> None:
        if self.conditions_table.selectedIndexes():
            selected_material = int(
                self.conditions_table.item(self.conditions_table.currentRow(), 1).text()
            )
            EditMaterialDialog(material_datastore[selected_material]).exec()

    def _rename_click_handler(self) -> None:
        if self.conditions_table.selectedIndexes():
            self.conditions_table.editItem(
                self.conditions_table.item(self.conditions_table.currentRow(), 0)
            )

    def _material_renamed(self, row: int, column: int) -> None:
        material_id = int(self.conditions_table.item(row, 1).text())
        new_name = self.conditions_table.item(row, column).text()

        old_name = material_datastore[material_id].name
        material_datastore[material_id].name = new_name

        logging.info(f"Material {old_name} renamed to {new_name}")

    def _add_material(self, key: int, value: Material) -> Material:
        materials_count = len(material_datastore)
        # we want to use the cellChanged signal for when a material is renamed but,
        # using insertRow emits that signal, so we can temporarily block signals whilst
        # we're doing this
        self.conditions_table.blockSignals(True)
        self.conditions_table.insertRow(materials_count - 1)
        self.conditions_table.setItem(
            materials_count - 1, 0, QTableWidgetItem(value.name)
        )
        self.conditions_table.setItem(
            materials_count - 1, 1, QTableWidgetItem(str(key))
        )
        self.conditions_table.blockSignals(False)
        return value

    def _get_selected_material_id(self) -> int | None:
        if not self.conditions_table.selectedIndexes():
            return None
        return int(
            self.conditions_table.item(self.conditions_table.currentRow(), 1).text()
        )

    def _copy_click_handler(self) -> None:
        if (selected_material_id := self._get_selected_material_id()) is None:
            return

        selected_material = material_datastore[selected_material_id]
        material = Material(
            name=selected_material.name + "_copy",
            properties=deepcopy(selected_material.properties),
        )
        material_datastore.add(material)

        logging.info(f"Created copy of material {selected_material.name}")

    def _delete_click_handler(self) -> None:
        if (selected_material_id := self._get_selected_material_id()) is None:
            return

        logging.info(f"Deleting material {material_datastore[selected_material_id]}")

        del material_datastore[selected_material_id]
        row = self.conditions_table.currentIndex().row()

        self.conditions_table.removeRow(row)
