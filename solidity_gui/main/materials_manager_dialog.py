from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QTableWidget, QVBoxLayout

class MaterialsManagerDialog(QDialog):
    """Dialog for managing materials.

    Materials can be created from, and will populate this dialog.
    """

    def __init__(self):
        """Initialise a new dialog."""
        super().__init__()
        self.setWindowTitle("Materials Manager")
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.materials = dict()

        materials_table = QTableWidget()
        materials_table.setColumnCount(2)
        materials_table.setHorizontalHeaderLabels(["Name", "ID"])

        layout.addWidget(materials_table)

        self.create_button = QPushButton("Create")
        self.edit_button = QPushButton("Edit")
        self.rename_button = QPushButton("Rename")
        self.copy_button = QPushButton("Copy")
        self.delete_button = QPushButton("Delete")

        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.create_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.rename_button)
        buttons_layout.addWidget(self.copy_button)
        buttons_layout.addWidget(self.delete_button)

        layout.addLayout(buttons_layout)

        self.create_button.clicked.connect(self._click_handler)

    def _create_click_handler(self):
        EditMaterialDialog()._exec()