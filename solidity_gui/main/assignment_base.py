"""Module for the AssignmentBase class."""

from dataclasses import dataclass


@dataclass
class AssignmentBase:
    """A base class for Assignment datastructures."""

    cell_set_name: str
