"""Module for the MaterialsManagerDialog class."""
from typing import Dict

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
from .material import Material


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

        self.materials: Dict[str, Material] = {}

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

        pub.subscribe(self._add_material, "materials.add")
        pub.subscribe(self._toggle_property, "property.toggle_enabled")

    def _create_click_handler(self) -> None:
        CreateMaterialDialog().exec()

    def _edit_click_handler(self) -> None:
        if self.materials_table.selectedIndexes():
            selected_material = self.materials_table.item(
                self.materials_table.currentRow(), 0
            ).text()
            print(selected_material)
            EditMaterialDialog(self.materials[selected_material]).exec()

    def _rename_click_handler(self) -> None:
        if self.materials_table.selectedIndexes():
            self.materials_table.editItem(
                self.materials_table.item(self.materials_table.currentRow(), 0)
            )

    def _material_renamed(self, row: int, column: int) -> None:
        material_id = self.materials_table.item(row, 1).text()
        new_name = self.materials_table.item(row, column).text()

        for name, material in self.materials.items():
            if material.id == int(material_id):
                old_name = name
                break

        if old_name != new_name:
            self.materials[new_name] = self.materials[old_name]
            self.materials[new_name].name = new_name
            del self.materials[old_name]

    def _add_material(self, material: str) -> None:
        material_unique_id = (
            max([material.id for material in self.materials.values()], default=0) + 1
        )
        self.materials[material] = Material(name=material, id=material_unique_id)
        materials_count = len(self.materials)
        # we want to use the cellChanged signal for when a material is renamed but,
        # using insertRow emits that signal, so we can temporarily block signals whilst
        # we're doing this
        self.materials_table.blockSignals(True)
        self.materials_table.insertRow(materials_count - 1)
        self.materials_table.setItem(materials_count - 1, 0, QTableWidgetItem(material))
        self.materials_table.setItem(
            materials_count - 1, 1, QTableWidgetItem(str(material_unique_id))
        )
        self.materials_table.blockSignals(False)

    def _copy_click_handler(self) -> None:
        if self.materials_table.selectedIndexes():
            selected_material = self.materials_table.item(
                self.materials_table.currentRow(), 0
            ).text()

            self._add_material(selected_material + "_copy")
            self.materials[selected_material + "_copy"].properties = self.materials[
                selected_material
            ].properties

    def _delete_click_handler(self) -> None:
        if self.materials_table.selectedIndexes():
            selected_material = self.materials_table.item(
                self.materials_table.currentRow(), 0
            ).text()
            self.materials.pop(selected_material, None)
            row = self.materials_table.currentIndex().row()
            self.materials_table.removeRow(row)

    def _toggle_property(self, material: str, property: str) -> None:
        self.materials[material].properties[property].enabled ^= True
