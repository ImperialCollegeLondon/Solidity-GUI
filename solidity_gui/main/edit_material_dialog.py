from pubsub import pub
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QTreeView, QVBoxLayout

from .material import Material

class PropertiesTree(QTreeView):
    def __init__(self, material: Material, enabled_properties: bool):
        """Initialise a new PropertiesTree"""
        super().__init__()

        self.setHeaderHidden(True)

        self.base_model = QStandardItemModel()
        self.root_node = self.base_model.invisibleRootItem()

        self.categories = dict()
        for property_name, property_settings in material.properties.items():
            if property_settings.enabled is enabled_properties:
                property_node = QStandardItem(property_name)
                property_node.setEditable(False)
                self.categories.setdefault(property_settings.category, {}).setdefault(property_name, property_node)

        self.category_nodes = dict()
        for category, properties_dict in self.categories.items():
            category_node = QStandardItem(category)
            category_node.setSelectable(False)
            category_node.setEditable(False)
            self.category_nodes[category] = QStandardItem(category)
            [category_node.appendRow(property_node) for property_node in properties_dict.values()]
            self.root_node.appendRow(category_node)

        self.setModel(self.base_model)
        self.expandAll()

class EditMaterialDialog(QDialog):
    """Dialog for editing a material."""

    def __init__(self, material: Material):
        """Initialise a new dialog."""
        super().__init__()
        self.material = material
        self.setWindowTitle(f"Editing {material.name}")

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.disabled_properties_tree = PropertiesTree(material, False)
        layout.addWidget(self.disabled_properties_tree)

        buttons_layout = QVBoxLayout()
        add_button = QPushButton("&Add >>")
        add_button.clicked.connect(self._add_clicked)
        remove_button = QPushButton("&<< Remove")
        remove_button.clicked.connect(self._remove_clicked)
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(remove_button)
        layout.addLayout(buttons_layout)

        self.enabled_properties_tree = PropertiesTree(material, True)
        layout.addWidget(self.enabled_properties_tree)

        self.properties_trees = {"enabled": self.enabled_properties_tree,
                                "disabled": self.disabled_properties_tree}

    def _add_clicked(self):
        self._toggle_property(move_from="disabled", move_to="enabled")

    def _remove_clicked(self):
        self._toggle_property(move_from="enabled", move_to="disabled")

    def _toggle_property(self, move_from: str, move_to: str):
        from_tree = self.properties_trees[move_from]
        to_tree = self.properties_trees[move_to]
        selected_property_index = from_tree.selectedIndexes()[0]
        selected_property_text = from_tree.base_model.itemFromIndex(selected_property_index).text()
        category = self.material.properties[selected_property_text].category
        category_item = from_tree.base_model.itemFromIndex(
            selected_property_index.parent()
        )
        selected_property_item = category_item.takeRow(
            selected_property_index.row()
        )[0]

        pub.sendMessage("property.toggle_enabled", material=self.material.name, property=selected_property_text)
        if category in to_tree.category_nodes:
            # Give ownership of the property QStandardItem to the "to" tree
            to_tree.base_model.findItems(category)[0].appendRow(selected_property_item)

        else:
            # If the category does not exist in the "to" tree, we create it and add it to both the model and the category_nodes dict
            category_node = QStandardItem(category)
            category_node.setSelectable(False)
            category_node.setEditable(False)
            category_node.appendRow(selected_property_item)
            to_tree.root_node.appendRow(category_node)
            to_tree.expandAll()
            to_tree.category_nodes[category] = category_node

        # Remove the category from the "from" tree if it no longer has any children
        if not category_item.hasChildren():
            from_tree.root_node.removeRow(
                category_item.row()
            )
            from_tree.category_nodes.pop(category)
