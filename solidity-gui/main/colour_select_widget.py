import numpy as np
from PySide6.QtWidgets import QComboBox
from vtk.util import numpy_support


class ColourSelectWidget(QComboBox):
    def __init__(self, vtk_window, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vtk_window = vtk_window
        self.addItems(vtk_window.mesh.cell_sets.keys())

        self.currentTextChanged.connect(self._select_handler)

    def _select_handler(self):
        mesh = self.vtk_window.mesh
        selectedValue = self.currentText()
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
