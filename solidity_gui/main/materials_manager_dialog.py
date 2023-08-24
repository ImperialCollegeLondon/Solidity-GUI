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

from .create_material_dialog import CreateMaterialDialog
from .edit_material_dialog import EditMaterialDialog
from .material import Material, material_datastore


class MaterialsManagerDialog(QDialog):
    """Dialog for managing materials.

    Materials can be created from this dialog.
    Created Materials will be shown in the tree view in this dialog.
    """

    def __init__(self) -> None:
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle("Materials Manager")
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.materials_table = QTableWidget()
        # allow user to only select one row
        self.materials_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.materials_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # disable editing of table items
        self.materials_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.materials_table.setColumnCount(2)
        self.materials_table.setHorizontalHeaderLabels(["Name", "ID"])
        # by default, QTableWidgets display a row index
        # we can disable this since we are manually setting an ID later
        self.materials_table.verticalHeader().setVisible(False)
        # distribute the available space according to the
        # space requirement of each column
        header = self.materials_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        layout.addWidget(self.materials_table)

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

        self.materials_table.cellChanged.connect(self._material_renamed)

        for key, material in material_datastore.items():
            self._add_material(key, material)
        pub.subscribe(self._add_material, material_datastore.update_topic)

    def _create_click_handler(self) -> None:
        CreateMaterialDialog(material_datastore).exec()

    def _edit_click_handler(self) -> None:
        if self.materials_table.selectedIndexes():
            selected_material = int(
                self.materials_table.item(self.materials_table.currentRow(), 1).text()
            )
            EditMaterialDialog(material_datastore[selected_material]).exec()

    def _rename_click_handler(self) -> None:
        if self.materials_table.selectedIndexes():
            self.materials_table.editItem(
                self.materials_table.item(self.materials_table.currentRow(), 0)
            )

    def _material_renamed(self, row: int, column: int) -> None:
        material_id = int(self.materials_table.item(row, 1).text())
        new_name = self.materials_table.item(row, column).text()

        old_name = material_datastore[material_id].name
        material_datastore[material_id].name = new_name

        logging.info(f"Material {old_name} renamed to {new_name}")

    def _add_material(self, key: int, value: Material) -> Material:
        row_id = self.materials_table.rowCount()
        # we want to use the cellChanged signal for when a material is renamed but,
        # using insertRow emits that signal, so we can temporarily block signals whilst
        # we're doing this
        self.materials_table.blockSignals(True)
        self.materials_table.insertRow(row_id)
        self.materials_table.setItem(row_id, 0, QTableWidgetItem(value.name))
        self.materials_table.setItem(row_id, 1, QTableWidgetItem(str(key)))
        self.materials_table.blockSignals(False)
        return value

    def _get_selected_material_id(self) -> int | None:
        if not self.materials_table.selectedIndexes():
            return None
        return int(
            self.materials_table.item(self.materials_table.currentRow(), 1).text()
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
        row = self.materials_table.currentIndex().row()

        self.materials_table.removeRow(row)
