"""Dialog for adding simple geometric shapes."""

from typing import Dict, Set

from pubsub import pub
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QPushButton,
    QTreeView,
    QVBoxLayout,
)

from .edit_property_dialog import EditPropertyDialog
from .material import Material


class PropertiesTree(QTreeView):
    """Implementation of a tree view for enabling/disabling properties."""

    def __init__(self, material: Material, enabled_properties: bool):
        """Initialise a new PropertiesTree.

        Args:
          material: Material object from which to build this tree
          enabled_properties: builds enabled/disabled properties tree if true/false
        """
        super().__init__()

        self.setHeaderHidden(True)

        self.base_model = QStandardItemModel()
        self.root_node = self.base_model.invisibleRootItem()

        self.categories: Dict[str, QStandardItem] = {}
        for property_name, property_settings in material.properties.items():
            if property_settings.enabled is enabled_properties:
                property_node = QStandardItem(property_name)
                property_node.setEditable(False)
                self.categories.setdefault(property_settings.category, {}).setdefault(
                    property_name, property_node
                )

        self.category_nodes = dict()
        for category, properties_dict in self.categories.items():
            category_node = QStandardItem(category)
            category_node.setSelectable(False)
            category_node.setEditable(False)
            self.category_nodes[category] = QStandardItem(category)
            [
                category_node.appendRow(property_node)
                for property_node in properties_dict.values()
            ]
            self.root_node.appendRow(category_node)

        self.setModel(self.base_model)
        self.expandAll()


class EditMaterialDialog(QDialog):
    """Dialog for editing a material."""

    def __init__(self, material: Material):
        """Initialise a new dialog.

        Args:
            material: Material object for which properties this dialog will edit
        """
        super().__init__()
        self.material = material
        self.setWindowTitle(f"Editing {material.name}")

        layout = QVBoxLayout()
        self.setLayout(layout)

        tree_layout = QHBoxLayout()

        self.disabled_properties_tree = PropertiesTree(material, False)
        tree_layout.addWidget(self.disabled_properties_tree)

        buttons_layout = QVBoxLayout()
        add_button = QPushButton("&Add >>")
        add_button.clicked.connect(self._add_clicked)
        remove_button = QPushButton("<< &Remove")
        remove_button.clicked.connect(self._remove_clicked)
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(remove_button)
        tree_layout.addLayout(buttons_layout)

        self.enabled_properties_tree = PropertiesTree(material, True)
        tree_layout.addWidget(self.enabled_properties_tree)
        layout.addLayout(tree_layout)

        # add Save and Cancel buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Reset | QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )

        self.button_box.accepted.connect(
            self._save_clicked
        )  # type: ignore[attr-defined]
        self.button_box.rejected.connect(self.close)  # type: ignore[attr-defined]
        self.button_box.button(QDialogButtonBox.Reset).clicked.connect(
            self._reset_clicked
        )

        edit_button = QPushButton("Edit Property")
        edit_button.clicked.connect(self._edit_button_clicked)

        layout.addWidget(self.button_box)
        layout.addWidget(edit_button)

        self.properties_trees = {
            "enabled": self.enabled_properties_tree,
            "disabled": self.disabled_properties_tree,
        }

        # This set holds all the properties which have been toggled.
        # If the user presses the save button, then we can iterate over this set later
        # and send the toggle signal for the materials dict for each set element.
        # If the user cancels then we simply do nothing with this set.
        self.toggled_properties: Set[str] = set()

    def _add_clicked(self) -> None:
        self._toggle_property(
            from_tree=self.disabled_properties_tree,
            to_tree=self.enabled_properties_tree,
        )

    def _remove_clicked(self) -> None:
        self._toggle_property(
            from_tree=self.enabled_properties_tree,
            to_tree=self.disabled_properties_tree,
        )

    def _toggle_property(
        self, from_tree: PropertiesTree, to_tree: PropertiesTree
    ) -> None:
        if not from_tree.selectedIndexes():
            return
        selected_property_index = from_tree.selectedIndexes()[0]
        selected_property_text = from_tree.base_model.itemFromIndex(
            selected_property_index
        ).text()
        category = self.material.properties[selected_property_text].category
        category_item = from_tree.base_model.itemFromIndex(
            selected_property_index.parent()
        )
        selected_property_item = category_item.takeRow(selected_property_index.row())[0]

        if category in to_tree.category_nodes:
            # give ownership of the property QStandardItem to the "to" tree
            to_tree.base_model.findItems(category)[0].appendRow(selected_property_item)

        else:
            # if the category does not exist in the "to" tree, we create it and add it
            # to both the model and the category_nodes dict
            category_node = QStandardItem(category)
            category_node.setSelectable(False)
            category_node.setEditable(False)
            category_node.appendRow(selected_property_item)
            to_tree.root_node.appendRow(category_node)
            to_tree.expandAll()
            to_tree.category_nodes[category] = category_node

        # Remove the category from the "from" tree if it no longer has any children
        if not category_item.hasChildren():
            from_tree.root_node.removeRow(category_item.row())
            from_tree.category_nodes.pop(category)

        if selected_property_text in self.toggled_properties:
            self.toggled_properties.discard(selected_property_text)
        else:
            self.toggled_properties.add(selected_property_text)

    def _save_clicked(self) -> None:
        for property in self.toggled_properties:
            pub.sendMessage(
                "property.toggle_enabled",
                material=self.material.name,
                property=property,
            )

        self.close()

    def _reset_clicked(self) -> None:
        self.done(QDialog.Rejected)
        dialog = EditMaterialDialog(self.material)
        dialog.exec_()

    def _edit_button_clicked(self) -> None:
        from_tree = self.disabled_properties_tree
        selected_property_index = from_tree.selectedIndexes()[0]
        selected_property_text = from_tree.base_model.itemFromIndex(
            selected_property_index
        ).text()
        property = self.material.properties[selected_property_text]

        EditPropertyDialog(property).exec_()
