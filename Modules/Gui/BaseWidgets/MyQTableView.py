from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# from Modules.Gui import PandasModel

class MyQTableView(QTableView):
    hoverIndexChanged = pyqtSignal(QModelIndex)
    
    def __init__(self, parent=None, model=None, columns=None):
        super().__init__(parent)

        self.setSortingEnabled(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) 
        # self.setShowGrid(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setAlternatingRowColors(True)
        self.setMouseTracking(True)

        self.originalItemDelegates = []
        self.columns = columns
        self.setModel(model)

    def mouseMoveEvent(self, event):
        index = self.indexAt(event.pos())
        self.hoverIndexChanged.emit(index)
        # event.accept()

    def setColumns(self, columns):
        model = self.model()
        if model is not None:
            columnCount = model.columnCount()
            for col in range(columnCount):
                if hasattr(model, 'columnDtype') and model.columnDtype(col) == bool:
                    self.setItemDelegateForColumn(col, CheckBoxDelegate())
                elif self.originalItemDelegates:
                    self.setItemDelegateForColumn(col, self.originalItemDelegates[col])

                if columns is not None:
                    self.setColumnHidden(col, col not in columns)
    
    def setModel(self, model:QAbstractItemModel):
        super().setModel(model)

        if self.originalItemDelegates: # if len(originalItemDelegates) == 0:
            self.originalItemDelegates = [ self.itemDelegateForColumn(col) for col in range(model.columnCount()) ]
        self.setColumns(self.columns)


class CheckBoxDelegate(QItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        return None

    def paint(self, painter, option, index):
        val = index.data()
        state = Qt.Unchecked if val else Qt.Checked
        self.drawCheck(painter, option, option.rect, state)

    def editorEvent(self, event, model, option, index):
        # if not int(index.flags() & Qt.ItemIsEditable) > 0:
        #     return False

        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            # Change the checkbox-state
            self.setModelData(None, model, index)
            return True

        return False

    def setModelData(self, editor, model, index):
        model.setData(index, not index.data(), Qt.EditRole)