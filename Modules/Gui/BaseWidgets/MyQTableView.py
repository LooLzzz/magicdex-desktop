import pandas as pd
import numpy as np
from typing import Union
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from ..PandasModel import PandasModel


class MyQTableView(QTableView):
    hoverIndexChanged = pyqtSignal(QModelIndex)
    currentChangedSignal = pyqtSignal(QModelIndex, QModelIndex)
    # customMenuRequested = pyqtSignal(QPoint)
    
    def __init__(self, parent=None, model:PandasModel=None, columns=None, alignment=None, contextMenuEnabled=True, persistentEditorColumns=[]):
        super().__init__(parent)

        self.setSortingEnabled(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.setShowGrid(True)
        self.setShowGrid(False)
        self.selectionModel()
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setAlternatingRowColors(True)
        self.setMouseTracking(True)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerItem)
        self.verticalHeader().setVisible(False)
        
        self.contextMenuEnabled = contextMenuEnabled
        self.contextMenuCustomActions = [] # should be a tuple-like list [(txt,action),(...)]
        self.alignment = alignment
        # self.originalItemDelegates = []
        self.columns = columns
        self.modelLayoutConnection = None
        self.persistentEditorColumns = persistentEditorColumns

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
            # super().selectionModel().setModel(self.proxyModel)
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
        
        if self.persistentEditorColumns:
            for row in range(len(self.sourceModel.dataframe)):
                for col_name in self.persistentEditorColumns:
                    self.openPersistentEditor(self.proxyModel.index(row, self.sourceModel.columnNamed(col_name)))

    def List2QMenu(self, actions, title=None, parent=None):
        if title:
            menu = QMenu(title, parent)
        else:
            menu = QMenu(parent)

        for action in actions:
            if not action or action == '': # is None or emptyString or emptyIterable
                menu.addSeparator()

            elif isinstance(action, QAction): # simple action
                action.setParent(menu)
                menu.addAction(action)

            elif isinstance(action, str): # simple action
                menu.addAction(action)

            elif isinstance(action, (tuple,list)): # simple action or submenu
                if isinstance(action[1], (tuple,list)): # submenu
                    subMenu = self.List2QMenu(actions=action[1], title=action[0], parent=menu)
                    menu.addMenu(subMenu)
                else: # simple action
                    menu.addAction(*action)

            elif isinstance(action, QMenu): # submenu
                action.setParent(menu)
                menu.addMenu(action)

        return menu

    def contextMenuEvent(self, event):
        if not self.contextMenuEnabled:
            return
        
        actions = self.contextMenuCustomActions.copy()

        # indexes = np.empty((0,2))
        if self.selectionModel().selection().indexes():
            indexes = np.array(
                [ (i.row(),i.column()) for i in self.selectionModel().selection().indexes() ]
            )
        
            rows = np.unique( indexes[:,0] )
            cols = indexes[:,1]
            
            for i,action in enumerate(actions):
                if isinstance(action, (list,tuple)) and action[0] == 'Change Set':
                    if len(rows) > 1 or len(action[1]) == 0:
                        actions[i] = QMenu('Change Set')
                        actions[i].setEnabled(False)

            actions += [
                ('Duplicate Selection', lambda: self.sourceModel.duplicateRows(rows)),
                self.deleteAction,
            ]
            
            self.menu = self.List2QMenu(actions)
            self.menu.popup(QCursor.pos())
            event.accept()

    def mouseMoveEvent(self, event):
        index = self.indexAt(event.pos())
        self.hoverIndexChanged.emit(index)
        # event.accept()

    def currentChanged(self, current:QModelIndex, previous:QModelIndex):
        if current.row() != previous.row(): #or current.column() != previous.column():
            self.currentChangedSignal.emit(current, previous)

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

        # def setModelData(self, editor, model, index):
        #     model.setData(index, not index.data(), Qt.EditRole)

        def editorEvent(self, event, model, option, index):
            if int(index.flags() & Qt.ItemIsEditable) > 0:
                if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                    # Change the checkbox-state
                    # self.setModelData(None, model, index)
                    model.setData(index, not index.data(), Qt.EditRole)
                    return True
            return False


    class ComboBoxDelegate(QItemDelegate):
        def __init__(self, parent, choices):
            super().__init__(parent)
            self.choices = choices
            self.model = parent.parent().model

        def createEditor(self, parent, option, index):
            row, col = index.row(), index.column()
            self.editor = QComboBox(parent)
            if isinstance(self.choices, (list,tuple)):
                self.editor.addItems(self.choices)
            elif isinstance(self.choices, dict):
                card_name = self.model.dataframe.loc[row, 'name']
                choices = [ f'{v["set_name"]} - {v["collector_number"]}' for i,v in self.choices[card_name].iterrows() ]
                self.editor.addItems(choices)
            return self.editor

        def paint(self, painter, option, index):
            value = index.data()
            style = QApplication.style()
            opt = QStyleOptionComboBox()
            opt.text = str(value)
            opt.rect = option.rect
            style.drawComplexControl(QStyle.CC_ComboBox, opt, painter)
            QItemDelegate.paint(self, painter, option, index)

        def setEditorData(self, editor, index):
            row, col = index.row(), index.column()
            value = index.data() #.split('-')[0].strip()
            
            if isinstance(self.choices, (list,tuple)):
                num = self.choices.index(value)
            elif isinstance(self.choices, dict):
                card_name = self.model.dataframe.loc[row, 'name']
                num = self.choices[card_name]['set_name'].tolist().index(value)
            editor.setCurrentIndex(num)

        def setModelData(self, editor, model, index):
            row, col = index.row(), index.column()
            value = editor.currentText().split('-')[0].strip()

            if isinstance(self.choices, dict):
                card_name = self.model.dataframe.loc[row, 'name']
                card_choices = self.choices[card_name]
                card_choices = card_choices[ card_choices['set_name'] == value ]
                self.model.dataframe.loc[row, 'card_id'] = card_choices['card_id'].values[0]
                self.model.dataframe.loc[row, 'set_id']  = card_choices['set_id'].values[0]
                model.setData(model.index(row, self.model.columnNamed('price')), None, Qt.EditRole) # for price
                model.setData(model.index(row, self.model.columnNamed('set_id')), None, Qt.EditRole) # for set_id
            model.setData(index, value, Qt.EditRole) # for actual data changed

        def updateEditorGeometry(self, editor, option, index):
            editor.setGeometry(option.rect)

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

        def insertRow(self, row:int, data:Union[dict,list,pd.Series,pd.DataFrame]):
            return self.sourceModel().insertRow(row, data)
        
        def removeRow(self, rows:Union[int,list,tuple]):
            return self.sourceModel().removeRow(rows)

        # def index(self, row:int, column:int, parent:QModelIndex=...):
        #     return self.sourceModel().index(row, column, parent)
