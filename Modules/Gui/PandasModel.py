# import pickle
# from typing import Iterable
# import numpy as np
import pandas as pd
from typing import Union
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_integer_dtype, is_float_dtype, is_bool_dtype
# from pandas.core.tools.numeric import to_numeric
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from ..Gui.QWorkerThread import QWorkerThread
from ..BusinessLogic.ScryfallApi import fetch_data as fetch

class PandasModel(QAbstractTableModel):
    CompleterRole = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent=None, df=None, enable_tooltip=False):
        super().__init__(parent)
        self.enable_tooltip = enable_tooltip
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
        row, col = index.row(), index.column()
        if index.isValid() and role == Qt.EditRole \
                and row in range(len(self.currentItems))\
                and col in range(len(self.currentItems.columns)):
            if self.columnName(col) == 'amount' and value < 1:
                self.currentItems.iloc[row, col] = 1
                self.dataChanged.emit(index, index)
            elif self.columnName(col) == 'foil':
                self.currentItems.iloc[row, col] = value
                self.dataChanged.emit(index, index)
                if 'price' in self.currentItems.columns:
                    self.currentItems.loc[row, 'price'] = None
                    price_index = self.index(row, self.columnNamed('price'))
                    self.dataChanged.emit(price_index, price_index)
            else:
                self.currentItems.iloc[row, col] = value
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
        else:
            if row >= 0:
                upper = self.dataframe[:row]
                lower = self.dataframe[row:]
                df = pd.concat([upper, data, lower]).reset_index(drop=True)
                self.setDataFrame(df)
            else:
                df = pd.concat([self.dataframe, data]).reset_index(drop=True)
                self.setDataFrame(df)

    def removeRow(self, rows:Union[int,list,tuple]):
        if self.currentItems is None:
            return None
        
        if isinstance(rows, int):
            rows = [rows]

        rows = self.currentItems.iloc[rows]
        df = self.dataframe.drop(index=rows.index).reset_index(drop=True)
        self.setDataFrame(df)
        return rows

    def duplicateRows(self, rows):
        df = self.dataframe
        dup_rows = self.currentItems.iloc[rows]
        upper = df.iloc[:rows[-1]]
        lower = df.iloc[rows[-1]:]
        
        df = pd.concat([ upper, dup_rows, lower ]).reset_index(drop=True)
        self.setDataFrame(df)

    def flags(self, index):
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        if index.isValid():
            row, col = index.row(), index.column()
            colname = self.columnName(col)
            if colname == 'amount' \
                    or colname == 'foil':
                flags |= Qt.ItemIsEditable
        
        return flags


    def data(self, index, role):
        def _card_price_callback(res):
            idx = []
            for _,card in res.iterrows():
                i = self.dataframe.index[ (self.dataframe['card_id'] == card['card_id']) & (self.dataframe['foil'] == card['foil']) ]
                self.dataframe.loc[i, 'price'] = card['price']

                idx += i.values.tolist()
            
            # idx = self.dataframe.index[ self.dataframe['card_id'].isin(res['card_id']) ]
            # self.dataframe.loc[idx, 'price'] = res['price'].values
            idx_topleft  = self.index( min(idx), self.columnNamed('price') )
            idx_botright = self.index( max(idx), self.columnNamed('price') )
            self.dataChanged.emit(idx_topleft, idx_botright)
        ########################################################

        if index.isValid():
            col_data:pd.Series = self.currentItems.iloc[:, index.column()]
            row_data:pd.Series = self.currentItems.iloc[index.row()]
            cell_value = self.currentItems.iloc[index.row(), index.column()]

            if role == Qt.DisplayRole:
                if is_bool_dtype(col_data):
                    return bool(cell_value)
                if col_data.name == 'price':
                    if pd.isna(cell_value):
                        worker = QWorkerThread(parent=self, task=fetch.fetch_card_prices, cards_df=row_data)
                        worker.results.connect(_card_price_callback)
                        worker.finished.connect(worker.deleteLater)
                        worker.start()
                    return f'{cell_value*row_data["amount"]:.2f}$' if pd.notna(cell_value) and cell_value > 0 else '-'
                return str(cell_value)
            elif role == Qt.EditRole:
                if is_integer_dtype(col_data):
                    return int(cell_value)
                if is_float_dtype(col_data):
                    return float(cell_value)
                return str(cell_value)
            elif role == Qt.ToolTipRole and self.enable_tooltip:
                txt = f'{row_data["name"]} [{row_data["set_id"].upper()}]'
                if row_data['foil']:
                    txt += ' [F]'
                if not pd.isna(row_data['price']) and row_data['price'] >= 0:
                    txt += f' - {row_data["price"]:.2f}$'
                return txt
        return QVariant()

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            colname = str(self.currentItems.columns[col]) \
                        .replace('_', ' ') \
                        .title()
            if colname == 'Collector Number':
                return 'Collector No.'
            return colname
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
                            row_flags = row_flags | (float(val) == col)
                        except ValueError:
                            pass
                    if is_string_dtype(col.dtype):
                        row_flags = row_flags | col.str.lower().str.contains(str(val).lower()) 

            self.layoutAboutToBeChanged.emit()
            self.currentItems = self.dataframe.loc[row_flags]
            # self.currentItems.reset_index(inplace=True, drop=True)
            self.layoutChanged.emit()
