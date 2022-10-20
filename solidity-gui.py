#import sys

import numpy as np
import pygmsh
import vtk
from vtk.util import numpy_support

from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer
)

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFontComboBox,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFrame,
)

def get_orientation(ren):
    p = dict()
    camera = ren.GetActiveCamera()
    p['position'] = camera.GetPosition()
    p['focal point'] = camera.GetFocalPoint()
    p['view up'] = camera.GetViewUp()
    p['distance'] = camera.GetDistance()
    p['clipping range'] = camera.GetClippingRange()
    p['orientation'] = camera.GetOrientation()
    return p

def set_orientation(ren, p):
    camera = ren.GetActiveCamera()
    camera.SetPosition(p['position'])
    camera.SetFocalPoint(p['focal point'])
    camera.SetViewUp(p['view up'])
    camera.SetDistance(p['distance'])
    camera.SetClippingRange(p['clipping range'])

class resetView_widget(QWidget):
    def __init__(self,parent,layout, ren, iren, original_orientation):
        super(resetView_widget, self).__init__()
        self.resetView=QPushButton("Reset view",parent)
        def handler():
            self.reset_camera(ren, iren, original_orientation)
        self.resetView.clicked.connect(handler)

        layout.addWidget(self.resetView)

    def reset_camera(self, ren, iren, original_orientation):
        set_orientation(ren, original_orientation)
        ren.ResetCamera()
        iren.ReInitialize()

class colourSelect_widget(QWidget):
    def __init__(self,parent,layout, ren, iren, mesh, mapper, ugrid):
        super(colourSelect_widget, self).__init__()

        # Drop-down list of mesh cell sets
        self.sidesComboBox = QComboBox(parent)
        self.sidesComboBox.addItems(mesh.cell_sets.keys())
        layout.addWidget(self.sidesComboBox)

        def handler():
            self.select_side(ren, iren, parent, mesh, mapper, ugrid)
        self.sidesComboBox.currentTextChanged.connect(handler)

        layout.addWidget(self.sidesComboBox)

    def select_side(self, ren, iren, parent, mesh, mapper, ugrid):
        selectedValue = self.sidesComboBox.currentText()
        surface_point_ids = parent.get_point_ids_in_surface(selectedValue, mesh)
        surface_uniq_point_ids = set(surface_point_ids.reshape(surface_point_ids.size))

        # colour points in surface
        point_colours = np.zeros(mesh.points.shape[0])
        point_colours[np.array(list(surface_uniq_point_ids))] = 1.0
        mapper.SetScalarModeToUsePointData()
        ugrid.GetPointData().SetScalars(numpy_support.numpy_to_vtk(point_colours))

        ren.ResetCamera()
        iren.ReInitialize()

# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):

    def get_point_ids_in_surface(self, name, mesh):
        triangles = mesh.cells[1]
        surface_cell_ids = mesh.cell_sets[name][1]
        return triangles.data[surface_cell_ids]

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Widgets App")

        self.vl = QVBoxLayout()
        widgets = [
            QCheckBox,
            QDateEdit,
            QDateTimeEdit,
            QDial,
            QDoubleSpinBox,
            QFontComboBox,
            QLCDNumber,
            QLabel,
            QLineEdit,
            QProgressBar,
            QPushButton,
            QRadioButton,
            QSlider,
            QSpinBox,
            QTimeEdit,
        ]

        for w in widgets:
            self.vl.addWidget(w())

        layout = QHBoxLayout()
        layout.setSpacing(20)
        layout.addLayout(self.vl)

        self.frame = QFrame()

        self.vtkLayout = QVBoxLayout()
        vtkWidget = QVTKRenderWindowInteractor()
        self.vtkLayout.addWidget(vtkWidget)

        layout.addLayout(self.vtkLayout)

        with pygmsh.geo.Geometry() as geom:

            bit_bottom = geom.add_circle(
                x0=[0.0, 0.0], radius=0.1, mesh_size=0.05, num_sections=3
            )
            bit_top, bit_volume, bit_sides = geom.extrude(
                bit_bottom.plane_surface, translation_axis=[0, 0, 1]
            )

            geom.add_physical(bit_bottom.plane_surface, "bit_bottom")
            geom.add_physical(bit_top, "bit_top")
            geom.add_physical(bit_volume, "bit_volume")
            for i, surface in enumerate(bit_sides):
                geom.add_physical(surface, f"bit_side{i}")

            box = geom.add_box(
                x0=-0.5,
                x1=0.5,
                y0=-0.5,
                y1=0.5,
                z0=1.3,
                z1=2.3,
                mesh_size=0.05,
            )
            geom.add_physical(box.volume, "box_volume")
            for i, surface in enumerate(box.surface_loop.surfaces):
                geom.add_physical(surface, f"box_side{i}")
            mesh = geom.generate_mesh()

            mesh2 = mesh.copy()
            mesh2.cell_sets = {}
            mesh2.write("test.vtu")

        def get_points_in_surface(name, mesh):
            return mesh.points[get_point_ids_in_surface(name, mesh)]

        filename = "test.vtu"
        reader = vtk.vtkXMLUnstructuredGridReader()
        reader.SetFileName(filename)
        # reader.SetInputString(tmp.getvalue())
        reader.Update()
        ugrid = reader.GetOutput()

        # Create the LUT for scalars to colors
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(2)
        lut.SetTableRange(0, 1)
        lut.Build()
        lut.SetTableValue(0, 1, 1, 1, 1)  # White
        lut.SetTableValue(1, 1, 0, 0, 1)  # Red

        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(ugrid)
        mapper.UseLookupTableScalarRangeOn()
        mapper.SetLookupTable(lut)

        surface_name = "box_side3"
        surface_point_ids = self.get_point_ids_in_surface(surface_name, mesh)
        surface_uniq_point_ids = set(surface_point_ids.reshape(surface_point_ids.size))
        surface_cells = mesh.cell_sets[surface_name][1]

        # colour points in surface
        point_colours = np.zeros(mesh.points.shape[0])
        point_colours[np.array(list(surface_uniq_point_ids))] = 1.0
        mapper.SetScalarModeToUsePointData()
        ugrid.GetPointData().SetScalars(numpy_support.numpy_to_vtk(point_colours))

        # # colour triangles of surface
        # cell_colours = np.array([])
        # for cell_block in mesh.cells:
        #     colour_array = np.zeros(cell_block.data.shape[0])
        #     if cell_block.type == "triangle":
        #         colour_array[surface_cells] = 1.0
        #     cell_colours = np.concatenate([cell_colours, colour_array])
        # mapper.SetScalarModeToUseCellData()
        # ugrid.GetCellData().SetScalars(numpy_support.numpy_to_vtk(cell_colours))

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        ren = vtk.vtkRenderer()
        ren.SetBackground(0.1, 0.2, 0.4)
        ren.AddActor(actor)

        ren.GetActiveCamera().Elevation(110)

        vtkWidget.GetRenderWindow().AddRenderer(ren)
        self.iren = vtkWidget.GetRenderWindow().GetInteractor()

        self.frame.setLayout(layout)
        self.setCentralWidget(self.frame)

        self.show()
        self.iren.Initialize()

        ren.ResetCamera()

        original_orientation = get_orientation(ren)
        resetView_widget(self, self.vl, ren, self.iren, original_orientation)

        colourSelect_widget(self, self.vl, ren, self.iren, mesh, mapper, ugrid)

app = QApplication()
window = MainWindow()
#window.show()

app.exec_()
