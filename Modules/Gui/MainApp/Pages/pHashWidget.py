import pandas as pd
# import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import Config

from Modules.BusinessLogic import pHash
from Modules.Gui import MyQWidget
from ...QWorkerThread import QWorkerThread
from ...PandasModel import PandasModel

class pHashWidget(MyQWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)

        layout = QVBoxLayout()
        self.setLayout(layout)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        self.text_box = QTextEdit()
        self.text_box.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_box.setLineWrapMode(QTextEdit.NoWrap)
        self.text_box.setFixedHeight(25)
        self.text_box.textChanged.connect(self.filterTextChanged)
        hbox.addWidget(self.text_box, alignment=Qt.AlignLeft)

        self.lbl_rowCount = QLabel('0 Entries')
        hbox.addWidget(self.lbl_rowCount, alignment=Qt.AlignRight)

        self.model = PandasModel(parent=self, df=None)
        self.tableView = QTableView(parent=self)
        self.tableView.setSortingEnabled(True)
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) 
        self.tableView.setShowGrid(False) 
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setModel(self.model)
        layout.addWidget(self.tableView)

    def filterTextChanged(self):
        txt = self.text_box.toPlainText()
        self.model.setFilter(txt, columns=['name', 'set', 'collector_number'])
        self.lbl_rowCount.setText(f'{self.model.rowCount()} Entries')

    def load_phash(self, update_flag):
        def _task(update_flag):
            print('\n', 'loading phash..')
            df = pHash.get_pHash_df(update=update_flag)
            df['phash'] = df['phash'].apply(lambda x: x.astype('uint8'))
            return df
        
        def _getWorkerResults(df):
            self.model = PandasModel(parent=self, df=df)
            self.tableView.setModel(self.model)
            self.lbl_rowCount.setText(f'{self.model.rowCount()} Entries')
            self.tableView.update()

        self.worker = QWorkerThread(self, _task, update_flag)
        self.worker.results.connect(_getWorkerResults)
        self.worker.start()
        
    def onShow(self):
        self.root_window.setWindowTitle('pHash Viewer')
        # self.root_window.setFixedSize(941, 700)
        self.root_window.resize(941, 700)
        
        if self.model.dataframe is None:
            self.load_phash(False)