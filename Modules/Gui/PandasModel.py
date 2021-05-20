# import pickle
# from typing import Iterable
# import numpy as np
import pandas as pd
from typing import Union
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
        self.filterKwargs = {}

    def setDataFrame(self, df:pd.DataFrame):
        # df = pd.api.types.infer_dtype
        if len(df) == 1:
            df = df.infer_objects()
        
        self.layoutAboutToBeChanged.emit()
        self.dataframe = df
        self.currentItems = df
        self.setFilter(**self.filterKwargs)
        self.layoutChanged.emit()

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

    def insertRow(self, row:int, data:Union[dict,list,pd.Series,pd.DataFrame]):
        if not isinstance(data, pd.DataFrame):
            if isinstance(data, (list, pd.Series)):
                data = pd.DataFrame(data)
            elif isinstance(data, dict):
                data = pd.DataFrame([data])
            else:
                raise ValueError(f'expected {{list | dict | pd.Series | pd.DataFrame}}, got {type(data)}')
        
        if self.dataframe is None:
            self.setDataFrame(data)
        elif row == -1:
            df = pd.concat([self.dataframe, data]).reset_index(drop=True)
            self.setDataFrame(df)
        else:
            upper = self.dataframe[:row]
            lower = self.dataframe[row:]
            df = pd.concat([upper, data, lower]).reset_index(drop=True)
            self.setDataFrame(df)

    def removeRow(self, rows:Union[int,list,tuple]):
        if self.currentItems is None:
            return None
        
        if isinstance(rows, int):
            rows = [rows]

        rows = self.currentItems.iloc[rows]
        df = self.dataframe.drop(index=rows.index)
        self.setDataFrame(df)
        return rows

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            col_data:pd.Series = self.currentItems.iloc[:,index.column()]
            if role == Qt.DisplayRole:
                val = self.currentItems.iloc[index.row(), index.column()]
                if not is_bool_dtype(col_data):
                    val = str(val)
                return val
        return QVariant()

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

    def columnName(self, column:int):
        '''
        converts `col_index` to `col_name`
        :param column: index of column
        :return: name of column
        '''
        return self.dataframe.columns[column]

    def columnNamed(self, column:str):
        '''
        converts `col_name` to `col_index`
        :param column: name of column
        :return: index of column
        '''
        if self.dataframe is not None:
            for i,colname in enumerate(self.dataframe):
                if column == colname:
                    return i
        return None

    def setFilter(self, val=None, columns=None):
        if val is None:
            return
        
        self.filterKwargs = {'val':val, 'columns':columns}
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
            # self.currentItems.reset_index(inplace=True, drop=True)
            self.layoutChanged.emit()
