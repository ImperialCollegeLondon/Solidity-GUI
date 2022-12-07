"""Code to display a mesh within a VTK window."""
import os
from tempfile import NamedTemporaryFile
from typing import Any

import numpy as np
import pygmsh
import vtk
from meshio import CellBlock, Mesh
from numpy.typing import NDArray
from PySide6.QtWidgets import QVBoxLayout
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util import numpy_support


def generate_mesh() -> Mesh:
    """Generates a mesh consisting of a cylinder and a cube."""
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

        return geom.generate_mesh()


def save_as_vtu(mesh: Mesh, filename: str) -> None:
    """Saves a mesh to a file.

    Args:
        mesh: The mesh to be saved
        filename: The name of the file to be saved
    """
    mesh2 = mesh.copy()
    mesh2.cell_sets = {}
    mesh2.write(filename)


class VTKWindow(QVBoxLayout):
    """A frame containing a VTK window."""

    def get_point_ids_in_surface(self, name: str, mesh: Mesh) -> NDArray[Any]:
        """Gets the points IDs of a mesh surface by name.

        Args:
            name: Name of the mesh surface
            mesh: The mesh object containing the surface
        """
        triangles: CellBlock = mesh.cells[1]
        surface_cell_ids = mesh.cell_sets[name][1]
        return triangles.data[surface_cell_ids]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create new VTKWindow."""
        super().__init__(*args, **kwargs)

        vtkWidget = QVTKRenderWindowInteractor()
        self.addWidget(vtkWidget)

        self.mesh = generate_mesh()
        with NamedTemporaryFile(suffix=".vtu", delete=False) as f:
            filename = f.name

        try:
            # Save the mesh to disk...
            save_as_vtu(self.mesh, filename)

            # ...and read it back in again
            reader = vtk.vtkXMLUnstructuredGridReader()
            reader.SetFileName(filename)
            reader.Update()
            self.ugrid = reader.GetOutput()
        finally:
            # Delete the file now that we've finished with it
            os.unlink(filename)

        # Create the LUT for scalars to colors
        self.lut = vtk.vtkLookupTable()
        self.lut.SetNumberOfTableValues(2)
        self.lut.SetTableRange(0, 1)
        self.lut.Build()
        self.lut.SetTableValue(0, 1, 1, 1, 1)  # White
        self.lut.SetTableValue(1, 1, 0, 0, 1)  # Red

        self.mapper = vtk.vtkDataSetMapper()
        self.mapper.SetInputData(self.ugrid)
        self.mapper.UseLookupTableScalarRangeOn()
        self.mapper.SetLookupTable(self.lut)

        surface_name = list(self.mesh.cell_sets.keys())[0]
        surface_point_ids = self.get_point_ids_in_surface(surface_name, self.mesh)
        surface_uniq_point_ids = set(surface_point_ids.reshape(surface_point_ids.size))

        # colour points in surface
        point_colours = np.zeros(self.mesh.points.shape[0])
        point_colours[np.array(list(surface_uniq_point_ids))] = 1.0
        self.mapper.SetScalarModeToUsePointData()
        self.ugrid.GetPointData().SetScalars(numpy_support.numpy_to_vtk(point_colours))

        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)

        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(0.1, 0.2, 0.4)
        self.ren.AddActor(self.actor)
        self.ren.GetActiveCamera().Elevation(110)
        self.ren.ResetCamera()

        vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = vtkWidget.GetRenderWindow().GetInteractor()
        self.iren.Initialize()
