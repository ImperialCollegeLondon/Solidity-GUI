"""Submodule for FormInfo and FieldInfo datastructures.

These classes provide a minimal datastructure containing the required information to
render a form within the GUI and to pass data back to Form classes for processing.
"""

from dataclasses import dataclass, field
from typing import Union

from PySide6.QtWidgets import QWidget


@dataclass
class FieldInfo:
    """Required data to render a form field within the GUI."""

    input: list[QWidget]
    header: str | None = None
    errors: dict[int, list[str]] = field(default_factory=dict)
    description: str | None = None
    _enabled: bool = True

    @property
    def enabled(self) -> bool:
        """Whether the field is disabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set disabled value and call setDisabled on all QWidgets in self.input."""
        self._enabled = value
        for inp in self.input:
            inp.setEnabled(value)


@dataclass
class FormInfo:
    """Required data to render a form within the GUI."""

    fields: dict[str, Union[FieldInfo, "FormInfo"]]
    schema_errors: list[str] = field(default_factory=list)
    header: str | None = None
    single_choice: bool = False
