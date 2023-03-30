"""Provides a custom VTK interactor style which allows for changing between modes."""
from pubsub import pub
from vtk import vtkInteractorStyleTrackballCamera, vtkRenderWindowInteractor


class CustomInteractorStyle(vtkInteractorStyleTrackballCamera):
    """A vtkInteractorStyle which allows for switching between pan, rotate and zoom.

    Based on the behaviour of vtkInteractorStyleTrackballCamera.
    """

    _INTERACT_FUNC_NAMES = {"pan": "Pan", "rotate": "Rotate", "zoom": "Dolly"}
    """The suffixes for function names used for different interact modes."""

    def __init__(self, initial_interact_mode: str = "pan") -> None:
        """Create a new CustomInteractorStyle.

        Args:
            initial_interact_mode: The initial interact mode (pan, rotate or zoom)
        """
        super().__init__()

        self._interact_func_suffix: str = self._INTERACT_FUNC_NAMES[
            initial_interact_mode
        ]
        """The suffix for the function name for the current interact mode."""

        # Override default handlers for left mouse button click
        self.AddObserver("LeftButtonPressEvent", self._mouse_down)
        self.AddObserver("LeftButtonReleaseEvent", self._mouse_up)

        # Change interact mode when relevant toolbar button is clicked
        pub.subscribe(self._change_interact_mode, "window.change_mode")

    def _change_interact_mode(self, mode: str) -> None:
        self._interact_func_suffix = self._INTERACT_FUNC_NAMES[mode]

    def _mouse_down(self, obj: vtkRenderWindowInteractor, event: str) -> None:
        """Start the relevant interaction behaviour when mouse is clicked."""
        func = getattr(self, f"Start{self._interact_func_suffix}")
        func()

    def _mouse_up(self, obj: vtkRenderWindowInteractor, event: str) -> None:
        """Stop the relevant interaction behaviour when mouse button is released."""
        func = getattr(self, f"End{self._interact_func_suffix}")
        func()
