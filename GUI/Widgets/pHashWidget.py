# import sys
import pandas as pd
# import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import Config
from p_hash import pHash
from .CustomWidget import CustomWidget
from .PandasModel import PandasModel

# sys.path.insert(1, '../..')

class pHashWidget(CustomWidget):
    def __init__(self, parent, root_window):
        CustomWidget.__init__(self, parent, root_window)
        
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # filename = f'{Config.cards_path}/pHash/border_crop.pickle'

        self.tableView = QTableView(parent=self)
        self.tableView.setSortingEnabled(True)
        # self.model = PandasModel(parent=self, filepath=filename)
        # self.model = PandasModel(parent=self, df=pHash.get_pHash_df())
        self.model = PandasModel(parent=self, df=None)
        # self.model.worker.finished.connect(self.worker_finished)
        # self.model.layoutChanged.connect(self.onModelChanged)
        self.tableView.setModel(self.model)
        layout.addWidget(self.tableView)

    def update_phash(self):
        self.worker = self._WorkerThread(parent=self, update=True)
        self.worker.results.connect(self.getWorkerResults)
        self.worker.start()
        
    def getWorkerResults(self, df):
        self.model = PandasModel(parent=self, df=df)
        self.tableView.setModel(self.model)
        # print(f'pHash loaded, last update: {self.model.date_updated}')

    def onHiddenChange(self, invoker, *args, **kwargs):
        if self.isHidden():
            pass
        else:
            self.root_window.setWindowTitle('pHash View')
            self.root_window.setFixedSize(941, 700)
            
            if self.model.dataframe is not None:
                print('loading phash..')
                self.worker = self._WorkerThread(parent=self, update=False)
                self.worker.results.connect(self.getWorkerResults)
                self.worker.start()

    
    class _WorkerThread(QThread):
        results = pyqtSignal(pd.DataFrame)
        
        def __init__(self, parent, update):
            super().__init__(parent)
            self.update_flag = update

        def run(self):
            df = pHash.get_pHash_df(update=self.update_flag)
            self.results.emit(df)