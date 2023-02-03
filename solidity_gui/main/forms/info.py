"""Submodule for FormInfo and FieldInfo datastructures.

These classes provide a minimal datastructure containing the required information to
render a form within the GUI and to pass data back to Form classes for processing.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, cast

from PySide6.QtWidgets import QWidget


@dataclass
class FieldInfo:
    """Required data to render a form field within the GUI."""

    input: QWidget | List[QWidget]
    header: Optional[str] = None
    # below cast is needed to workaround https://github.com/python/mypy/issues/11923
    errors: List[str] | Dict[int, List[str]] = cast(
        List[str], field(default_factory=list)
    )
    description: Optional[str] = None


@dataclass
class FormInfo:
    """Required data to render a form within the GUI."""

    fields: Dict[str, FieldInfo]
    schema_errors: List[str] = field(default_factory=list)
