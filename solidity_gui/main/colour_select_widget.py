"""Code for a QComboBox widget to highlight cell_sets in a VTKWindow."""
from typing import Any

import numpy as np
from meshio import Mesh
from pubsub import pub
from PySide6.QtWidgets import QComboBox
from vtk.util import numpy_support

from .vtk_window import VTKWindow


class ColourSelectWidget(QComboBox):
    """QComboBox for highlighting a surface, populated from a mesh's cell_sets."""

    def __init__(self, vtk_window: VTKWindow, *args: Any, **kwargs: Any) -> None:
        """Create new ColourSelectWidget.

        Args:
            vtk_window: The VTKWindow which this widget interacts with.
        """
        super().__init__(*args, **kwargs)

        self.vtk_window = vtk_window

        self.currentTextChanged.connect(self._select_handler)
        pub.subscribe(self._set_items, "mesh.updated")

    def _select_handler(self) -> None:
        mesh = self.vtk_window.mesh
        if not mesh:
            return

        selectedValue = self.currentText()
        if not selectedValue:
            return
        surface_point_ids = self.vtk_window.get_point_ids_in_surface(
            selectedValue, mesh
        )
        surface_uniq_point_ids = set(surface_point_ids.reshape(surface_point_ids.size))

        # colour points in surface
        point_colours = np.zeros(mesh.points.shape[0])
        point_colours[np.array(list(surface_uniq_point_ids))] = 1.0
        self.vtk_window.mapper.SetScalarModeToUsePointData()
        self.vtk_window.ugrid.GetPointData().SetScalars(
            numpy_support.numpy_to_vtk(point_colours)
        )
        self.vtk_window.ren.ResetCamera()
        self.vtk_window.iren.ReInitialize()

    def _set_items(self, mesh: Mesh) -> None:
        self.clear()
        self.addItems(mesh.cell_sets.keys())
