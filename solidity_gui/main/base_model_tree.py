from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QHeaderView, QTreeView, QVBoxLayout

class BaseModelTree(QVBoxLayout):
    def __init__(self, num_models=0, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setFixedWidth(200)

        self.base_model = QStandardItemModel()
        self.root_node = self.base_model.invisibleRootItem()
        for _ in range(num_models):
            self._add_model()
        self.tree_view.setModel(self.base_model)
        self.tree_view.expandAll()
        self.addWidget(self.tree_view)

    def _add_model(self):
        new_model_node = QStandardItem(f"Model #{self.root_node.rowCount()+1}")

        new_model_node.appendRow(QStandardItem("Part"))
        new_model_node.appendRow(QStandardItem("Properties"))
        new_model_node.appendRow(QStandardItem("Mesh"))
        new_model_node.appendRow(QStandardItem("Assembly"))
        new_model_node.appendRow(QStandardItem("Step"))
        new_model_node.appendRow(QStandardItem("Conditions"))
        new_model_node.appendRow(QStandardItem("Interaction"))
        new_model_node.appendRow(QStandardItem("Jobs"))
        new_model_node.appendRow(QStandardItem("Results"))

        self.root_node.appendRow(new_model_node)