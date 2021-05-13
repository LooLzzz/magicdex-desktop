import pandas as pd
# import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import Config
from Modules import pHash
from Modules.Gui import MyQWidget
from ...QWorkerThread import QWorkerThread
from ...PandasModel import PandasModel

class pHashWidget(MyQWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.model = PandasModel(parent=self, df=None)
        self.tableView = QTableView(parent=self)
        self.tableView.setSortingEnabled(True)
        self.tableView.setModel(self.model)
        layout.addWidget(self.tableView)

    def load_phash(self, update_flag):
        def _getWorkerResults(df):
            df['phash'] = df['phash'].apply(lambda x: x.astype('uint8'))
            self.model = PandasModel(parent=self, df=df)
            self.tableView.setModel(self.model)
            self.tableView.update()

        print('loading phash..')
        self.worker = QWorkerThread(self, lambda update_flag: pHash.get_pHash_df(update=update_flag), update_flag)
        self.worker.results.connect(_getWorkerResults)
        self.worker.start()
        
    def onShow(self):
        self.root_window.setWindowTitle('pHash Viewer')
        # self.root_window.setFixedSize(941, 700)
        self.root_window.resize(941, 700)
        
        if self.model.dataframe is None:
            self.load_phash(False)