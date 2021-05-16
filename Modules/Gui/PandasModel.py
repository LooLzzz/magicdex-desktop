# import pickle
# from typing import Iterable
# import numpy as np
import pandas as pd
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_bool_dtype
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class PandasModel(QAbstractTableModel):
    CompleterRole = Qt.ItemDataRole.UserRole + 1

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

    def setData(self, index, value, role):
        if index.isValid() and role == Qt.EditRole \
                and index.row() in range(len(self.currentItems))\
                and index.column() in range(len(self.currentItems.columns)):
            self.currentItems.iloc[index.row(),index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            col_data:pd.Series = self.currentItems.iloc[:,index.column()]
            if role == Qt.DisplayRole:
                val = self.currentItems.iloc[index.row(), index.column()]
                if not is_bool_dtype(col_data):
                    val = str(val)
                return val
                # return str(self.currentItems.iloc[index.row(), index.column()])
            # elif role == Qt.TextAlignmentRole:
            #     if col_data.str.len().mean() < 20:
            #     return Qt.AlignCenter
        return QVariant()

    # def sibling(self, row, col, index:QModelIndex):
    #     if index.isValid():
    #         print(f'> sibling(row={row}, col={col}, index=(row={index.row()},col={index.column()}))')
    #     else:
    #         print(f'> sibling(row={row}, col={col})')
    #     return super().sibling(row, col, index)

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return str(self.currentItems.columns[col]) \
                    .replace('_', ' ') \
                    .title()
        return QVariant()

    def sort(self, column, order):
        if self.currentItems is not None:
            colname = self.currentItems.columns[column]
            order = (order == Qt.AscendingOrder)
            
            print(f"sorting by {colname} {'▲' if order else '▼'}")

            self.layoutAboutToBeChanged.emit()
            self.currentItems.sort_values(colname, ascending=order, inplace=True)
            self.currentItems.reset_index(inplace=True, drop=True)
            self.layoutChanged.emit()
    
    def columnDtype(self, column):
        if self.currentItems is not None:
            return self.currentItems.iloc[:,column].dtype
        return type(None)

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





















# # import pickle
# from typing import Iterable
# import pandas as pd
# from pandas.api.types import is_string_dtype, is_numeric_dtype
# import numpy as np
# from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
# from PyQt5.QtGui import *

# class PandasModel(QAbstractTableModel):
#     def __init__(self, parent=None, df=None):
#         super().__init__(parent)
#         self.dataframe = df
#         self.currentItems = df

#     def setDataframe(self, df):
#         self.dataframe = df
#         self.currentItems = df

#     def rowCount(self, parent=None):
#         if self.currentItems is not None:
#             return self.currentItems.shape[0]
#         return 0

#     def columnCount(self, parnet=None):
#         if self.currentItems is not None:
#             return self.currentItems.shape[1]
#         return 0

#     def data(self, index, role=Qt.DisplayRole):
#         if index.isValid():
#             if role == Qt.DisplayRole:
#                 return str(self.currentItems.iloc[index.row(), index.column()])
#         return None

#     def sibling(self, row, col, index:QModelIndex):
#         if index.isValid():
#             print(f'> sibling(row={row}, col={col}, index=(row={index.row()},col={index.column()}))')
#         else:
#             print(f'> sibling(row={row}, col={col})')
#         return super().sibling(row, col, index)
#         # if self.currentItems is not None:
#         #     if isinstance(col, str):
#         #         return self.currentItems.loc[col, row]
#         #     else:
#         #         return self.currentItems.iloc[col, row]
#         # return None

#     def headerData(self, col, orientation, role):
#         if orientation == Qt.Horizontal and role == Qt.DisplayRole:
#             return str(self.currentItems.columns[col]) \
#                     .replace('_', ' ') \
#                     .title()
#         return None

#     def sort(self, column, order):
#         if self.currentItems is not None:
#             colname = self.currentItems.columns.tolist()[column]
#             order = (order == Qt.AscendingOrder)
            
#             print(f"sorting by {colname} {'▲' if order else '▼'}")

#             self.layoutAboutToBeChanged.emit()
#             self.currentItems.sort_values(colname, ascending=order, inplace=True)
#             self.currentItems.reset_index(inplace=True, drop=True)
#             self.layoutChanged.emit()
    
#     def setFilter(self, val, columns=None):
#         if self.dataframe is not None:
#             if columns is None:
#                 columns = self.dataframe.columns
            
#             row_flags = pd.Series([False]*len(self.dataframe))
#             for colname in columns:
#                 if colname in self.dataframe:
#                     col = self.dataframe[colname]
#                     if is_numeric_dtype(col.dtype) or 'num' in colname:
#                         try:
#                             row_flags |= float(val) == col
#                         except ValueError:
#                             pass
#                     if is_string_dtype(col.dtype):
#                         row_flags |= col.str.lower().str.contains(str(val).lower()) 

#             self.layoutAboutToBeChanged.emit()
#             self.currentItems = self.dataframe.loc[row_flags]
#             self.currentItems.reset_index(inplace=True, drop=True)
#             self.layoutChanged.emit()
