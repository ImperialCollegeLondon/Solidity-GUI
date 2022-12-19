"""Code to display a mesh within a VTK window."""
import os
from dataclasses import dataclass
from tempfile import NamedTemporaryFile
from typing import Any, Optional, Tuple, Type

import numpy as np
import vtk
from meshio import CellBlock, Mesh
from numpy.typing import NDArray
from pubsub import pub
from PySide6.QtWidgets import QVBoxLayout
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util import numpy_support

from .. import config
from .geometry import Component, generate_mesh


def save_as_vtu(mesh: Mesh, filename: str) -> None:
    """Saves a mesh to a file.

    Args:
        mesh: The mesh to be saved
        filename: The name of the file to be saved
    """
    mesh2 = mesh.copy()
    mesh2.cell_sets = {}
    mesh2.write(filename)


@dataclass
class CameraOrientation:
    """Definition of CameraOrientation.

    Contains details of a vtkCamera's view port and focal point.

    Attributes:
        position: position of the camera in world coordinates
        focal_point: focal of the camera in world coordinates
        view_up: the view up direction for the camera
        distance: move the focal point so that it is the specified distance from the
        camera position
        clipping_range: the location of the near and far clipping planes along the
        direction of projection
        orientation: the orientation of the camera
    """

    position: Tuple[Type[float], Type[float], Type[float]]
    focal_point: Tuple[Type[float], Type[float], Type[float]]
    view_up: Tuple[Type[float], Type[float], Type[float]]
    distance: float
    clipping_range: Tuple[Type[float], Type[float]]
    orientation: Tuple[Type[float], Type[float], Type[float]]


class VTKWindow(QVBoxLayout):
    """A frame containing a VTK window."""

    unselected_lookup_value, selected_lookup_value = 0, 1

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
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(*config.BACKGROUND_COLOUR)
        self.ren.ResetCamera()
        self.actor = vtk.vtkActor()
        self.ren.AddActor(self.actor)

        vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = vtkWidget.GetRenderWindow().GetInteractor()
        self.iren.Initialize()
        self.mesh: Optional[Mesh] = None

        pub.subscribe(self._update_mesh, "mesh.update")
        pub.subscribe(self._colour_mesh_selection, "mesh.select")

    def _update_mesh(self, component: Component) -> None:
        self.mesh = generate_mesh([component])
        self.render_mesh(self.mesh)
        pub.sendMessage("mesh.updated", mesh=self.mesh)

    def render_mesh(self, mesh: Mesh) -> None:
        """Render a mesh within the VTKWindow.

        Args:
          mesh: The mesh to render
        """
        # Create the temporary file, but don't leave the file handle open
        with NamedTemporaryFile(suffix=".vtu", delete=False) as f:
            filename = f.name

        try:
            # Save the mesh to disk...
            save_as_vtu(mesh, filename)

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
        self.lut.SetTableRange(self.unselected_lookup_value, self.selected_lookup_value)
        self.lut.Build()
        self.lut.SetTableValue(self.unselected_lookup_value, *config.MESH_COLOUR)
        self.lut.SetTableValue(
            self.selected_lookup_value, *config.MESH_SELECTION_COLOUR
        )

        self.mapper = vtk.vtkDataSetMapper()
        self.mapper.SetInputData(self.ugrid)
        self.mapper.UseLookupTableScalarRangeOn()
        self.mapper.SetLookupTable(self.lut)

        self.actor.SetMapper(self.mapper)

        self.ren.ResetCamera()
        self.iren.ReInitialize()

    def _colour_mesh_selection(self, selection_name: str) -> None:
        """Update rendered mesh colours based on selected element."""
        if self.mesh is None:
            return

        surface_point_ids = np.unique(
            self.get_point_ids_in_surface(selection_name, self.mesh)
        )
        point_colours = np.full(self.mesh.points.shape[0], self.unselected_lookup_value)
        point_colours[surface_point_ids] = self.selected_lookup_value
        self.ugrid.GetPointData().SetScalars(numpy_support.numpy_to_vtk(point_colours))
        self.iren.ReInitialize()

    def set_camera_orientation(
        self, camera_orientation_settings: CameraOrientation
    ) -> None:
        """Resets a camera orientation for a vtkRenderer.

        Args:
            camera_orientation_settings: The Dict containing the camera orientation
            details
        """
        camera = self.ren.GetActiveCamera()
        camera.SetPosition(camera_orientation_settings.position)
        camera.SetFocalPoint(camera_orientation_settings.focal_point)
        camera.SetViewUp(camera_orientation_settings.view_up)
        camera.SetDistance(camera_orientation_settings.distance)
        camera.SetClippingRange(camera_orientation_settings.clipping_range)
        self.ren.ResetCamera()
        self.iren.ReInitialize()

    def get_camera_orientation(self) -> CameraOrientation:
        """Stores details on a camera orientation in a Dict."""
        camera = self.ren.GetActiveCamera()
        camera_orientation_settings = CameraOrientation(
            position=camera.GetPosition(),
            focal_point=camera.GetFocalPoint(),
            view_up=camera.GetViewUp(),
            distance=camera.GetDistance(),
            clipping_range=camera.GetClippingRange(),
            orientation=camera.GetOrientation(),
        )
        return camera_orientation_settings
