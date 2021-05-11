import pickle
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class PandasModel(QAbstractTableModel):
    def __init__(self, parent, df=None):
        QAbstractTableModel.__init__(self, parent)

        # self.date_updated = ''
        if df is None:
            self.dataframe = pd.DataFrame()
        else:
            self.dataframe = df
        # elif filepath is not None:
        #     self.dataframe = pd.DataFrame()
        #     self.filepath = filepath
        #     self.thread = QThread()
        #     self.worker = self._Worker(self.filepath)
        #     self.worker.moveToThread(self.thread)
        #     self.thread.started.connect(self.worker.run)
        #     # self.thread.finished.connect(self.thread.deleteLater)
        #     self.worker.finished.connect(self.thread.quit)
        #     self.worker.finished.connect(self.get_worker_results)
        #     # self.worker.finished.connect(self.worker.deleteLater)
        #     self.load_df_from_file()

    # def load_df_from_file(self):
    #     self.thread.start()

    # def get_worker_results(self, dataframe, date):
    #     self.layoutAboutToBeChanged.emit()
    #     self.dataframe = dataframe
    #     self.date_updated = date
    #     self.layoutChanged.emit()

    def rowCount(self, parent=None):
        return self.dataframe.shape[0]

    def columnCount(self, parnet=None):
        return self.dataframe.shape[1]

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
        colname = self.dataframe.columns.tolist()[column]
        order = (order == Qt.AscendingOrder)
        
        print(f'sorting by {colname} {"▲" if order else "▼"}')

        self.layoutAboutToBeChanged.emit()
        self.dataframe.sort_values(colname, ascending=order, inplace=True)
        self.dataframe.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()


    # class _Worker(QObject):
    #     finished = pyqtSignal(pd.DataFrame, str)
        
    #     def __init__(self, filepath):
    #         QObject.__init__(self)
    #         self.filepath = filepath

    #     def task(self):           
    #         with open(self.filepath, 'rb') as file:
    #             obj = pickle.load(file)
    #         date = obj['date']
    #         df = obj['data']
    #         df['phash'] = df['phash'].apply(lambda x: x.astype('uint8'))
            
    #         return (df, date)

    #     def run(self):
    #         df,date = self.task()
    #         self.finished.emit(df, date)













# import pickle
# from PyQt5.QtCore import *
# import pandas as pd

# class QDataFrameModel(QAbstractTableModel):
#     DtypeRole = Qt.UserRole + 1000
#     ValueRole = Qt.UserRole + 1001

#     def __init__(self, filepath, parent=None):
#         super(QDataFrameModel, self).__init__(parent)
        
#         with open(filepath) as file:
#             obj = pickle.load(file)
#             self._dataframe = obj['data']
#             self._date_updated = obj['date']

#     def setDataFrame(self, dataframe):
#         self.beginResetModel()
#         self._dataframe = dataframe.copy()
#         self.endResetModel()

#     def dataFrame(self):
#         return self._dataframe

#     dataFrame = pyqtProperty(pd.DataFrame, fget=dataFrame, fset=setDataFrame)

#     @pyqtSlot(int, Qt.Orientation, result=str)
#     def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
#         if role == Qt.DisplayRole:
#             if orientation == Qt.Horizontal:
#                 return self._dataframe.columns[section]
#             else:
#                 return str(self._dataframe.index[section])
#         return QVariant()

#     def rowCount(self, parent=QModelIndex()):
#         if parent.isValid():
#             return 0
#         return len(self._dataframe.index)

#     def columnCount(self, parent=QModelIndex()):
#         if parent.isValid():
#             return 0
#         return self._dataframe.columns.size

#     def data(self, index, role=Qt.DisplayRole):
#         if not index.isValid() or not (0 <= index.row() < self.rowCount() \
#             and 0 <= index.column() < self.columnCount()):
#             return QVariant()
#         row = self._dataframe.index[index.row()]
#         col = self._dataframe.columns[index.column()]
#         dt = self._dataframe[col].dtype

#         val = self._dataframe.iloc[row][col]
#         if role == Qt.DisplayRole:
#             return str(val)
#         elif role == QDataFrameModel.ValueRole:
#             return val
#         if role == QDataFrameModel.DtypeRole:
#             return dt
#         return QVariant()

#     def roleNames(self):
#         roles = {
#             Qt.DisplayRole: b'display',
#             QDataFrameModel.DtypeRole: b'dtype',
#             QDataFrameModel.ValueRole: b'value'
#         }
#         return roles

#     def sort(self, column, order):
#         colname = self._df.columns.tolist()[column]
#         self.layoutAboutToBeChanged.emit()
#         self._df.sort_values(colname, ascending= order == Qt.AscendingOrder, inplace=True)
#         self._df.reset_index(inplace=True, drop=True)
#         self.layoutChanged.emit()