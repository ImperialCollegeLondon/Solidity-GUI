from PySide6.QtWidgets import QDialog

class EditMaterialDialog(QDialog):
    """Dialog for editing a material."""

    def __init__(self, material: Material):
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle(f"Edit {material.name}")