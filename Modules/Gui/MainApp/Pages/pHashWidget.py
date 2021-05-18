import pandas as pd
# import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import Config

from Modules.BusinessLogic import pHash
from Modules.Gui import MyQWidget, MyQTableView
from ...PandasModel import PandasModel

class pHashWidget(MyQWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)

        layout = QVBoxLayout()
        self.setLayout(layout)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        self.text_box = QLineEdit()
        self.text_box.setPlaceholderText('Filter..')
        self.text_box.setMaximumWidth(250)
        self.text_box.textChanged.connect(self.filterTextChanged)
        hbox.addWidget(self.text_box)#, alignment=Qt.AlignLeft)

        self.lbl_rowCount = QLabel('0 Entries')
        hbox.addWidget(self.lbl_rowCount, alignment=Qt.AlignRight)

        self.model = PandasModel(parent=self, df=None)
        self.tableView = MyQTableView(parent=self, model=self.model)
        # self.tableView = QTableView(parent=self)
        # self.tableView.setModel(self.model)
        # self.tableView.hoverIndexChanged.connect(self.onHoverIndexChanged)
        
        layout.addWidget(self.tableView)

    def filterTextChanged(self, txt):
        # txt = self.text_box.toPlainText()
        self.model.setFilter(txt, columns=['name', 'set', 'collector_number'])
        self.lbl_rowCount.setText(f'{self.model.rowCount()} Entries')

    # def load_phash(self, update_flag):
    #     df = _task(update_flag=False)
    #     _getWorkerResults(df)
    #     self.worker = QWorkerThread(self, _task, update_flag)
    #     self.worker.results.connect(_getWorkerResults)
    #     self.worker.start()
        
    def onShow(self):
        self.root_window.setWindowTitle('pHash Viewer')
        # self.root_window.setFixedSize(941, 700)
        self.root_window.resize(1000, 700)
        
        def _getWorkerResults(df):
            df['phash'] = df['phash'].apply(lambda x: x.astype('uint8'))
            df['released_at'] = df['released_at'].dt.strftime('%Y-%m-%d')
            df['color_class_(BGR)'] = list(zip(df['b_classes'], df['g_classes'], df['r_classes']))
            df = df.drop(columns=['b_classes','g_classes','r_classes'])
            # df['test'] = pd.Series([ f%2==0 for f in range(len(df))])
            self.model = PandasModel(parent=self, df=df)
            self.tableView.setModel(self.model)
            self.lbl_rowCount.setText(f'{self.model.rowCount()} Entries')
            self.tableView.update()

        if self.model.dataframe is None:
            worker = pHash.get_pHash_df_qtasync(parent=self, callback=_getWorkerResults, update=False)
            # worker = pHash.get_pHash_df_qtasync(parent=self, callback=_getWorkerResults, update=True)
            worker.run()
            # self.load_phash(False)
