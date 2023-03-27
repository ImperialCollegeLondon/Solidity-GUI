"""Provides a custom VTK interactor style which allows for changing between modes."""
from pubsub import pub
from vtk import vtkInteractorStyleTrackballCamera, vtkRenderWindowInteractor


class CustomInteractorStyle(vtkInteractorStyleTrackballCamera):
    """A vtkInteractorStyle which allows for switching between pan, rotate and zoom.

    Based on the behaviour of vtkInteractorStyleTrackballCamera.
    """

    def __init__(self, initial_interact_mode: str = "pan") -> None:
        """Create a new CustomInteractorStyle.

        Args:
            initial_interact_mode: The initial interact mode (pan, rotate or zoom)
        """
        super().__init__()

        self.interact_mode: str
        """The current interaction mode.

        Can be pan, rotate or zoom.
        """
        self._change_interact_mode(initial_interact_mode)

        # Override default handlers for left mouse button click
        self.AddObserver("LeftButtonPressEvent", self._mouse_down)
        self.AddObserver("LeftButtonReleaseEvent", self._mouse_up)

        # Change interact mode when relevant toolbar button is clicked
        pub.subscribe(self._change_interact_mode, "window.change_mode")

    def _change_interact_mode(self, mode: str) -> None:
        if mode not in {"pan", "rotate", "zoom"}:
            raise ValueError("mode must be pan, rotate or zoom")

        self.interact_mode = mode

    def _mouse_down(self, obj: vtkRenderWindowInteractor, event: str) -> None:
        """Start the relevant interaction behaviour when mouse is clicked."""
        if self.interact_mode == "pan":
            self.StartPan()
        elif self.interact_mode == "rotate":
            self.StartRotate()
        elif self.interact_mode == "zoom":
            self.StartDolly()

    def _mouse_up(self, obj: vtkRenderWindowInteractor, event: str) -> None:
        """Stop the relevant interaction behaviour when mouse button is released."""
        if self.interact_mode == "pan":
            self.EndPan()
        elif self.interact_mode == "rotate":
            self.EndRotate()
        elif self.interact_mode == "zoom":
            self.EndDolly()
