"""Code to display a mesh within a VTK window."""
import os
from tempfile import NamedTemporaryFile
from typing import Any, List, Tuple

import numpy as np
import vtk
from meshio import CellBlock, Mesh
from numpy.typing import NDArray
from pubsub import pub
from PySide6.QtWidgets import QVBoxLayout
from vtk.util import numpy_support
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor

from .. import config
from .geometry import Component, MeshGenerator

Vector = Tuple[float, float, float]


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

        vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = vtkWidget.GetRenderWindow().GetInteractor()
        self.iren.Initialize()
        self.meshes: List[Mesh] = []
        self.components: List[Component] = []
        self.ugrids: List[vtk.vtkUnstructuredGrid] = []
        self.reset_camera()

        self._create_orientation_marker()

        self.mesh_generator = MeshGenerator()

        pub.subscribe(self._add_component_to_geometry_begin, "geometry.update")
        pub.subscribe(self._add_component_to_geometry_end, "geometry.meshing.end")
        pub.subscribe(self._create_mesh_from_geometry_begin, "mesh.create")
        pub.subscribe(self._create_mesh_from_geometry_end, "mesh.meshing.end")
        pub.subscribe(self._colour_mesh_selection, "mesh.select")
        pub.subscribe(self.reorient_camera, "camera.reorient")
        pub.subscribe(self.reset_camera, "camera.reset")

    def _add_component_to_geometry_begin(self, component: Component) -> None:
        """Add a new geometric component and render and display its rough mesh."""
        self.components.append(component)
        self.mesh_generator.start_mesh_generation(
            "geometry", [component], resolution=0.2
        )

    def _add_component_to_geometry_end(self, mesh: Mesh) -> None:
        self.meshes.append(mesh)
        self.render_mesh(mesh)
        pub.sendMessage("geometry.updated", mesh=mesh)

    def _create_mesh_from_geometry_begin(self) -> None:
        """Generate and display a high quality mesh from the current geometry."""
        if not self.components:
            return

        self.ugrids = []
        self.mesh_generator.start_mesh_generation(
            "mesh", self.components, resolution=0.05
        )

    def _create_mesh_from_geometry_end(self, mesh: Mesh) -> None:
        self.meshes = [mesh]
        for actor in self.ren.GetActors():
            self.ren.RemoveActor(actor)
        self.render_mesh(mesh)
        pub.sendMessage("mesh.updated", mesh=mesh)

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
            ugrid = reader.GetOutput()
        finally:
            # Delete the file now that we've finished with it
            os.unlink(filename)

        self.ugrids.append(ugrid)
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

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        self.ren.AddActor(actor)

        self.ren.ResetCamera()
        self.iren.ReInitialize()

    def _colour_mesh_selection(self, selection_name: str) -> None:
        """Update rendered mesh colours based on selected element."""
        for mesh, ugrid in zip(self.meshes, self.ugrids):
            point_colours = np.full(mesh.points.shape[0], self.unselected_lookup_value)
            try:
                surface_point_ids = np.unique(
                    self.get_point_ids_in_surface(selection_name, mesh)
                )
                point_colours[surface_point_ids] = self.selected_lookup_value
                self.iren.ReInitialize()
            except KeyError:
                pass

            ugrid.GetPointData().SetScalars(numpy_support.numpy_to_vtk(point_colours))
        self.iren.ReInitialize()

    def reset_camera(self) -> None:
        """Apply default settings to camera."""
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
        camera = self.ren.GetActiveCamera()
        focal_point = np.array(camera.GetFocalPoint())
        distance = camera.GetDistance()
        camera.SetPosition(distance * -np.array(orientation_vector) + focal_point)
        camera.SetViewUp(up_vector)
        self.iren.ReInitialize()
