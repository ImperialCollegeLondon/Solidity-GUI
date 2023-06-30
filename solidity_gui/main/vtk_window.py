"""Code to display a mesh within a VTK window."""
import logging
import os
from tempfile import NamedTemporaryFile
from typing import Any, Dict

import numpy as np
import vtk
from meshio import Mesh
from numpy.typing import NDArray
from pubsub import pub
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from vtk.util import numpy_support
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor

from .. import config
from .custom_interactor_style import CustomInteractorStyle
from .geometry import Vector
from .meshes import mesh_datastore


def save_as_vtu(mesh: Mesh, filename: str) -> None:
    """Saves a mesh to a file.

    Args:
        mesh: The mesh to be saved
        filename: The name of the file to be saved
    """
    mesh2 = mesh.copy()
    mesh2.cell_sets = {}
    mesh2.write(filename)


def make_axes_actor() -> vtkAxesActor:
    """Creates an axes actor for use as an orientation marker."""
    axes = vtkAxesActor()
    axes.SetShaftTypeToCylinder()
    axes.SetXAxisLabelText("X")
    axes.SetYAxisLabelText("Y")
    axes.SetZAxisLabelText("Z")
    axes.SetTotalLength(1.0, 1.0, 1.0)
    axes.SetCylinderRadius(0.5 * axes.GetCylinderRadius())
    axes.SetConeRadius(1.025 * axes.GetConeRadius())
    axes.SetSphereRadius(1.5 * axes.GetSphereRadius())
    return axes


def _set_cursor_to_busy() -> None:
    QApplication.setOverrideCursor(Qt.WaitCursor)


def _restore_cursor(mesh: Mesh = None) -> None:
    QApplication.restoreOverrideCursor()


class VTKWindow(QVTKRenderWindowInteractor):
    """A frame containing a VTK window."""

    unselected_lookup_value, selected_lookup_value = 0, 1

    def get_point_ids_for_cell_set(self, name: str, mesh: Mesh) -> NDArray[Any]:
        """Gets the points IDs of a mesh surface by name.

        Args:
            name: Name of the mesh surface
            mesh: The mesh object containing the surface
        """
        cell_set_dict = mesh.cell_sets_dict[name]
        cell_type = list(cell_set_dict.keys())[0]
        cell_set = cell_set_dict[cell_type]
        offset = mesh.cells_dict["triangle"].shape[0] if cell_type == "tetra" else 0
        return mesh.cells_dict[cell_type][cell_set - offset]

    def __init__(self) -> None:
        """Create new VTKWindow."""
        logging.info("Creating VTK frame")

        super().__init__()

        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(*config.BACKGROUND_COLOUR)

        self.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.GetRenderWindow().GetInteractor()

        # iren doesn't seem to hold a reference so we have to save this
        self.inter_style = CustomInteractorStyle()
        self.iren.SetInteractorStyle(self.inter_style)
        self.iren.Initialize()
        self.reset_camera()
        self.ugrids: Dict[str, vtk.vtkUnstructuredGrid] = {}
        self.actors: Dict[str, vtk.vtkActor] = {}
        self._create_orientation_marker()

        pub.subscribe(self._colour_mesh_selection, "mesh.select")
        pub.subscribe(self.reorient_camera, "camera.reorient")
        pub.subscribe(self.reset_camera, "camera.reset")

        # Set the mouse cursor to busy during meshing
        pub.subscribe(_set_cursor_to_busy, "mesh.meshing.begin")
        pub.subscribe(_set_cursor_to_busy, "geometry.meshing.begin")
        pub.subscribe(_restore_cursor, "mesh.meshing.end")
        pub.subscribe(_restore_cursor, "geometry.meshing.end")

        pub.subscribe(self.render_mesh, "geometry.updated")
        pub.subscribe(self.render_mesh, "mesh.updated")

    def render_mesh(self, mesh_name: str, mesh: Mesh) -> None:
        """Render a mesh within the VTKWindow.

        Args:
          mesh_name: The name of the mesh
          mesh: The mesh to render
        """
        logging.info("Rendering mesh")

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
            ugrid = reader.GetOutput()
        finally:
            # Delete the file now that we've finished with it
            os.unlink(filename)

        self.ugrids[mesh_name] = ugrid
        # Create the LUT for scalars to colors
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(2)
        lut.SetTableRange(self.unselected_lookup_value, self.selected_lookup_value)
        lut.Build()
        lut.SetTableValue(self.unselected_lookup_value, *config.MESH_COLOUR)
        lut.SetTableValue(self.selected_lookup_value, *config.MESH_SELECTION_COLOUR)

        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(ugrid)
        mapper.UseLookupTableScalarRangeOn()
        mapper.SetLookupTable(lut)

        if mesh_name in self.actors:
            self.ren.RemoveActor(self.actors[mesh_name])

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        self.ren.AddActor(actor)
        self.actors[mesh_name] = actor

        self.ren.ResetCamera()
        self.iren.ReInitialize()
        pub.sendMessage("mesh.rendered", mesh=mesh)

    def _colour_mesh_selection(self, selection_name: str) -> None:
        """Update rendered mesh colours based on selected element."""
        for mesh_name, mesh in mesh_datastore.items():
            point_colours = np.full(mesh.points.shape[0], self.unselected_lookup_value)
            try:
                point_ids = np.unique(
                    self.get_point_ids_for_cell_set(selection_name, mesh)
                )
                point_colours[point_ids] = self.selected_lookup_value
                self.iren.ReInitialize()
            except KeyError:
                pass

            self.ugrids[mesh_name].GetPointData().SetScalars(
                numpy_support.numpy_to_vtk(point_colours)
            )
        self.iren.ReInitialize()

    def reset_camera(self) -> None:
        """Apply default settings to camera."""
        logging.info("Resetting camera")

        self.ren.ResetCamera()
        self.reorient_camera(
            config.DEFAULT_ORIENTATION_VECTOR, config.DEFAULT_UP_VECTOR
        )

    def _create_orientation_marker(self) -> None:
        """Creates an orientation axes and displays it in the VTK window."""
        self.orientation_axes = make_axes_actor()
        self.om1 = vtkOrientationMarkerWidget()
        self.om1.SetOrientationMarker(self.orientation_axes)
        self.om1.SetInteractor(self.iren)
        self.om1.EnabledOn()
        self.om1.InteractiveOn()

    def reorient_camera(self, orientation_vector: Vector, up_vector: Vector) -> None:
        """Updates camera position to a new orientation whilst preserving focal point.

        Args:
            orientation_vector: new orientation w.r.t focal point. Passing a unit vector
                                will preserve the current distance from the focal point.
            up_vector: up direction of camera for new orientation.
        """
        logging.info("Reorienting camera")

        camera = self.ren.GetActiveCamera()
        focal_point = np.array(camera.GetFocalPoint())
        distance = camera.GetDistance()
        camera.SetPosition(distance * -np.array(orientation_vector) + focal_point)
        camera.SetViewUp(up_vector)
        self.iren.ReInitialize()
