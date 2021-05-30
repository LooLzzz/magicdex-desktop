import pandas as pd
import numpy as np
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from ..PandasModel import PandasModel


class MyQTableView(QTableView):
    hoverIndexChanged = pyqtSignal(QModelIndex)
    # customMenuRequested = pyqtSignal(QPoint)
    
    def __init__(self, parent=None, model:PandasModel=None, columns=None, alignment=None, contextMenuEnabled=True):
        super().__init__(parent)

        self.setSortingEnabled(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.setShowGrid(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setAlternatingRowColors(True)
        self.setMouseTracking(True)
        
        self.contextMenuEnabled = contextMenuEnabled
        self.contextMenuCustomActions = [] # should be a tuple-like list [(txt,action),(...)]
        self.alignment = alignment
        # self.originalItemDelegates = []
        self.columns = columns
        self.modelLayoutConnection = None

        self.deleteAction = QAction('Delete Selection', self)
        self.deleteAction.setShortcut('Delete')
        self.deleteAction.triggered.connect(lambda: self.sourceModel.removeRow(np.unique([ i.row() for i in self.selectionModel().selection().indexes() ])))
        self.addAction(self.deleteAction)

        self.setModel(model)

    def setModel(self, model:PandasModel):
        if self.modelLayoutConnection:
            self.model().disconnect(self.modelLayoutConnection)
        self.modelLayoutConnection = model.layoutChanged.connect(self.onModelLayoutChanged)
        self.sourceModel = model

        if self.alignment is not None:
            self.proxyModel = self.AlignmentProxyModel(sourceModel=model, alignment=self.alignment)
            super().setModel(self.proxyModel)
        else:
            super().setModel(model)

        # if self.originalItemDelegates: # if len(originalItemDelegates) == 0:
        #     self.originalItemDelegates = [ self.itemDelegateForColumn(col) for col in range(model.columnCount()) ]
        self.setColumns(self.columns)

    def onModelLayoutChanged(self, parents=None, hint:QAbstractTableModel.LayoutChangeHint=None):
        self.setModel(self.sourceModel)
        # model = self.sourceModel
        # if self.originalItemDelegates: # if len(originalItemDelegates) == 0:
        #     self.originalItemDelegates = [ self.itemDelegateForColumn(col) for col in range(model.columnCount()) ]
        # self.setColumns(self.columns)

    def contextMenuEvent(self, event):
        if self.contextMenuEnabled:
            # indexes = np.empty((0,2))
            if self.selectionModel().selection().indexes():
                indexes = np.array(
                    [ (i.row(),i.column()) for i in self.selectionModel().selection().indexes() ]
                )
            
                rows = indexes[:,0]
                cols = indexes[:,1]

                self.menu = QMenu(self)

                actions = self.contextMenuCustomActions + [
                    ('Duplicate Selection', lambda: self.sourceModel.duplicateRows(np.unique(rows))),
                    self.deleteAction,
                ]

                for item in actions:
                    if not item or item == '': # is None or emptyString or emptyIterable
                        self.menu.addSeparator()
                    elif isinstance(item, QAction):
                        self.menu.addAction(item)
                    elif isinstance(item, (tuple,list)):
                        self.menu.addAction(*item)
                    elif isinstance(item, (QMenu,str)):
                        self.menu.addMenu(item)
                
                self.menu.popup(QCursor.pos())
                event.accept()

    def mouseMoveEvent(self, event):
        index = self.indexAt(event.pos())
        self.hoverIndexChanged.emit(index)
        # event.accept()

    def setColumns(self, columns):
        model = self.sourceModel
        if model is not None:
            columnCount = model.columnCount()
            for col in range(columnCount):
                colname = model.columnName(col)
                # if hasattr(model, 'columnDtype') and model.columnDtype(col) == bool:
                #     self.setItemDelegateForColumn(col, self.CheckBoxDelegate())
                # elif self.originalItemDelegates:
                #     self.setItemDelegateForColumn(col, self.originalItemDelegates[col])

                if columns is not None:
                    if colname in columns:
                        self.showColumn(col)
                    else:
                        self.hideColumn(col)
        
        if columns is not None:
            self.columns = columns


    class CheckBoxDelegate(QItemDelegate):
        def createEditor(self, parent, option, index):
            return None

        def paint(self, painter, option, index):
            val = index.data()
            state = Qt.Checked if val else Qt.Unchecked
            self.drawCheck(painter, option, option.rect, state)

        def editorEvent(self, event, model, option, index):
            if int(index.flags() & Qt.ItemIsEditable) > 0:
                if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                    # Change the checkbox-state
                    self.setModelData(None, model, index)
                    return True
            return False

        def setModelData(self, editor, model, index):
            model.setData(index, not index.data(), Qt.EditRole)


    class AlignmentProxyModel(QIdentityProxyModel):
        def __init__(self, parent=None, sourceModel=None, alignment=Qt.AlignCenter):
            super().__init__(parent)
            self.alignment = alignment
            
            if sourceModel is not None:
                self.setSourceModel(sourceModel)

        def data(self, index, role):
            if role == Qt.TextAlignmentRole:
                return self.alignment
            return super().data(index, role)