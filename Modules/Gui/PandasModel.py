# import pickle
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class PandasModel(QAbstractTableModel):
    def __init__(self, parent, df=None):
        super().__init__(parent)
        self.dataframe = df

    def rowCount(self, parent=None):
        if self.dataframe is not None:
            return self.dataframe.shape[0]
        return 0

    def columnCount(self, parnet=None):
        if self.dataframe is not None:
            return self.dataframe.shape[1]
        return 0

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self.dataframe.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.dataframe.columns[col]
        return None

    def sort(self, column, order):
        if self.dataframe is not None:
            colname = self.dataframe.columns.tolist()[column]
            order = (order == Qt.AscendingOrder)
            
            print(f"sorting by {colname} {'▲' if order else '▼'}")

            self.layoutAboutToBeChanged.emit()
            self.dataframe.sort_values(colname, ascending=order, inplace=True)
            self.dataframe.reset_index(inplace=True, drop=True)
            self.layoutChanged.emit()