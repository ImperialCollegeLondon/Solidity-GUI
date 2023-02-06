from pubsub import pub
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout

from .create_material_dialog import CreateMaterialDialog
from .edit_material_dialog import EditMaterialDialog
from .material import Material

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

        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(2)
        self.materials_table.setHorizontalHeaderLabels(["Name", "ID"])
        # By default, QTableWidgets display a row index. We can disable this since we are manually setting an ID later
        self.materials_table.verticalHeader().setVisible(False)
        # Distribute the available space according to the space requirement of each column.
        self.materials_table.resizeColumnsToContents()

        layout.addWidget(self.materials_table)

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

        self.create_button.clicked.connect(self._create_click_handler)
        self.edit_button.clicked.connect(self._edit_click_handler)

        pub.subscribe(self._add_material, "materials.add")
        pub.subscribe(self._toggle_property, "property.toggle_enabled")

    def _create_click_handler(self): 
        CreateMaterialDialog().exec()

    def _edit_click_handler(self):
        selected_material = self.materials_table.item(self.materials_table.currentRow(), 0).text()
        EditMaterialDialog(self.materials[selected_material]).exec()

    def _add_material(self, material: str):
        self.materials[material] = Material(name=material)
        materials_count = len(self.materials)
        self.materials_table.insertRow(materials_count-1)
        self.materials_table.setItem(materials_count-1 , 0, QTableWidgetItem(material))
        self.materials_table.setItem(materials_count-1 , 1, QTableWidgetItem(str(materials_count)))
        self.materials_table.resizeColumnsToContents()

    def _toggle_property(self, material: str, property: str):
        self.materials[material].properties[property].enabled ^= True