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

from .create_initial_condition_dialog import CreateInitialConditionDialog
from .edit_initial_condition_dialog import EditInitialConditionDialog
from .initial_condition import InitialCondition, initial_condition_datastore


class InitialConditionsManagerDialog(QDialog):
    """Dialog for managing initial conditions.

    Initial conditions can be created from this dialog.
    """

    def __init__(self) -> None:
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle("Initial Conditions Manager")
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.table = QTableWidget()
        # allow user to only select one row
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # disable editing of table items
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "ID"])
        # by default, QTableWidgets display a row index
        # we can disable this since we are manually setting an ID later
        self.table.verticalHeader().setVisible(False)
        # distribute the available space according to the
        # space requirement of each column
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

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

        self.table.cellChanged.connect(self._condition_renamed)

        pub.subscribe(self._add_condition, initial_condition_datastore.update_topic)
        pub.subscribe(self._clear_conditions, "session.new")

    def _clear_conditions(self) -> None:
        self.table.setRowCount(0)

    def _create_click_handler(self) -> None:
        CreateInitialConditionDialog().exec()

    def _edit_click_handler(self) -> None:
        if self.table.selectedIndexes():
            selected_condition = int(self.table.item(self.table.currentRow(), 1).text())
            EditInitialConditionDialog(
                initial_condition_datastore[selected_condition]
            ).exec()
            self.table.item(self.table.currentRow(), 0).setText(
                initial_condition_datastore[selected_condition].name
            )

    def _rename_click_handler(self) -> None:
        if self.table.selectedIndexes():
            self.table.editItem(self.table.item(self.table.currentRow(), 0))

    def _condition_renamed(self, row: int, column: int) -> None:
        selected_condition = int(self.table.item(row, 1).text())
        new_name = self.table.item(row, column).text()

        old_name = initial_condition_datastore[selected_condition].name
        initial_condition_datastore[selected_condition].name = new_name

        logging.info(f"Condition {old_name} renamed to {new_name}")

    def _add_condition(self, key: int, value: InitialCondition) -> None:
        conditions_count = len(initial_condition_datastore)
        # we want to use the cellChanged signal for when a condition is renamed but,
        # using insertRow emits that signal, so we can temporarily block signals whilst
        # we're doing this
        self.table.blockSignals(True)
        self.table.insertRow(conditions_count - 1)
        self.table.setItem(conditions_count - 1, 0, QTableWidgetItem(value.name))
        self.table.setItem(conditions_count - 1, 1, QTableWidgetItem(str(key)))
        self.table.blockSignals(False)

    def _get_selected_condition_id(self) -> int | None:
        if not self.table.selectedIndexes():
            return None
        return int(self.table.item(self.table.currentRow(), 1).text())

    def _copy_click_handler(self) -> None:
        if (selected_condition_id := self._get_selected_condition_id()) is None:
            return

        selected_condition = initial_condition_datastore[selected_condition_id]
        condition = InitialCondition(
            name=selected_condition.name + "_copy",
            properties=deepcopy(selected_condition.properties),
        )
        initial_condition_datastore.add(condition)

        logging.info(f"Created copy of initial condition {selected_condition.name}")

    def _delete_click_handler(self) -> None:
        if (selected_condition_id := self._get_selected_condition_id()) is None:
            return

        logging.info(
            "Deleting initial condition "
            f"{initial_condition_datastore[selected_condition_id]}"
        )

        del initial_condition_datastore[selected_condition_id]
        row = self.table.currentIndex().row()

        self.table.removeRow(row)
