"""Module for AssignmentTable class."""
from collections.abc import Callable, Iterable

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from .assignment_base import AssignmentBase


class AssignmentTable(QTableWidget):
    """Table for the display of assignment datastructures."""

    def __init__(
        self, column_headers: list[str], getters: list[Callable[[AssignmentBase], str]]
    ):
        """Create a new AssignmentTable instance.

        Args:
          column_headers: header text for additional table columns
          getters: functions returning text for each column from an assignment instance
        """
        super().__init__()
        self.setColumnCount(len(column_headers) + 1)
        self.setHorizontalHeaderLabels(["Component"] + column_headers)
        self.setEditTriggers(
            QAbstractItemView.NoEditTriggers  # type: ignore[attr-defined]
        )
        self.horizontalHeader().setHighlightSections(False)
        self.setSelectionBehavior(
            QAbstractItemView.SelectRows  # type: ignore[attr-defined]
        )
        self.setSelectionMode(
            QAbstractItemView.SingleSelection  # type: ignore[attr-defined]
        )
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch  # type: ignore[attr-defined]
        )
        self.getters = getters

    def add_items(self, items: Iterable[AssignmentBase]) -> None:
        """Add assignment datastructures as table rows.

        Args:
          items: Assignment datastructures to add
        """
        for item in items:
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(item.cell_set_name))
            for i, getter in enumerate(self.getters, 1):
                self.setItem(row, i, QTableWidgetItem(str(getter(item))))
