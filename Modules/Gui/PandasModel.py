# import pickle
from typing import Iterable
import pandas as pd
from pandas.api.types import is_string_dtype, is_numeric_dtype
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class PandasModel(QAbstractTableModel):
    def __init__(self, parent=None, df=None):
        super().__init__(parent)
        self.dataframe = df
        self.currentItems = df

    def setDataframe(self, df):
        self.dataframe = df
        self.currentItems = df

    def rowCount(self, parent=None):
        if self.currentItems is not None:
            return self.currentItems.shape[0]
        return 0

    def columnCount(self, parnet=None):
        if self.currentItems is not None:
            return self.currentItems.shape[1]
        return 0

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self.currentItems.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.currentItems.columns[col]
        return None

    def sort(self, column, order):
        if self.currentItems is not None:
            colname = self.currentItems.columns.tolist()[column]
            order = (order == Qt.AscendingOrder)
            
            print(f"sorting by {colname} {'▲' if order else '▼'}")

            self.layoutAboutToBeChanged.emit()
            self.currentItems.sort_values(colname, ascending=order, inplace=True)
            self.currentItems.reset_index(inplace=True, drop=True)
            self.layoutChanged.emit()
    
    def setFilter(self, val, columns=None):
        if self.dataframe is not None:
            if columns is None:
                columns = self.dataframe.columns
            
            row_flags = pd.Series([False]*len(self.dataframe))
            for colname in columns:
                if colname in self.dataframe:
                    col = self.dataframe[colname]
                    if is_numeric_dtype(col.dtype) or 'num' in colname:
                        try:
                            row_flags |= float(val) == col
                        except ValueError:
                            pass
                    if is_string_dtype(col.dtype):
                        row_flags |= col.str.lower().str.contains(str(val).lower()) 

            self.layoutAboutToBeChanged.emit()
            self.currentItems = self.dataframe.loc[row_flags]
            self.currentItems.reset_index(inplace=True, drop=True)
            self.layoutChanged.emit()
