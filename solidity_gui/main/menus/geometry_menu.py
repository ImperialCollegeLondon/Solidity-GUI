"""Code to create the "Geometry" menu."""

from functools import partial

from PySide6.QtWidgets import QMenu

from ..load_geometry import load_geometry
from .menu_utils import create_action, create_shape_action


class GeometryMenu(QMenu):
    """Creates the "Geometry" menu."""

    def __init__(self) -> None:
        """Create the "Geometry" menu."""
        super().__init__("&Geometry")

        self.addAction(create_shape_action(self, "ball"))
        self.addAction(create_shape_action(self, "box"))
        self.addAction(create_shape_action(self, "cone"))
        self.addAction(create_shape_action(self, "cylinder"))

        import_geometry_action = create_action(
            self, "&Import Geometry from file", partial(load_geometry, self)
        )
        self.addAction(import_geometry_action)
