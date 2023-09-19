"""Defines the QComboBox subsclass MeshSelectionComboBox."""

from typing import Any

from pubsub import pub
from PySide6.QtWidgets import QComboBox


class MeshSelectionComboBox(QComboBox):
    """QComboBox for highlighting a surface, populated from a mesh's cell_sets."""

    def __init__(
        self, select_topic: str | None = None, *args: Any, **kwargs: Any
    ) -> None:
        """Create new MeshSelectionComboBox."""
        super().__init__(*args, **kwargs)

        self.currentTextChanged.connect(self._select_handler)
        self.textHighlighted.connect(self._highlight_handler)
        self.select_topic = select_topic

    def _select_handler(self, selected_text: str | None) -> None:
        if not selected_text:
            return

        if self.select_topic:
            pub.sendMessage(self.select_topic, cell_set_name=selected_text)

    def _highlight_handler(self, selected_text: str) -> None:
        pub.sendMessage("mesh.select_highlight", cell_set_name=selected_text)

    def showPopup(self) -> None:
        """Extend showPopup to highlight cell set when opened for not the first time."""
        super().showPopup()
        if selected_text := self.currentText():
            pub.sendMessage("mesh.select_highlight", cell_set_name=selected_text)

    def hidePopup(self) -> None:
        """Extend hidePopup to clear any mesh highlights."""
        super().hidePopup()
        pub.sendMessage("mesh.select_highlight", cell_set_name=None)
