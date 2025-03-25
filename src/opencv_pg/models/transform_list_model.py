import logging

from PySide6 import QtCore
from PySide6.QtCore import QAbstractListModel, Qt

log = logging.getLogger(__name__)


class TransformsModel(QAbstractListModel):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.items[index.row()].__name__
        return None
