from PySide6.QtWidgets import QPushButton


def set_orientation(ren, p):
    camera = ren.GetActiveCamera()
    camera.SetPosition(p["position"])
    camera.SetFocalPoint(p["focal point"])
    camera.SetViewUp(p["view up"])
    camera.SetDistance(p["distance"])
    camera.SetClippingRange(p["clipping range"])


def get_orientation(ren):
    p = dict()
    camera = ren.GetActiveCamera()
    p["position"] = camera.GetPosition()
    p["focal point"] = camera.GetFocalPoint()
    p["view up"] = camera.GetViewUp()
    p["distance"] = camera.GetDistance()
    p["clipping range"] = camera.GetClippingRange()
    p["orientation"] = camera.GetOrientation()
    return p


class ResetViewWidget(QPushButton):
    def __init__(self, vtk_window, *args, **kwargs):
        super().__init__("Reset view", *args, **kwargs)

        self.original_orientation = get_orientation(vtk_window.ren)
        self.vtk_window = vtk_window
        self.clicked.connect(self._click_handler)

    def _click_handler(self):

        set_orientation(self.vtk_window.ren, self.original_orientation)
        self.vtk_window.ren.ResetCamera()
        self.vtk_window.iren.ReInitialize()
