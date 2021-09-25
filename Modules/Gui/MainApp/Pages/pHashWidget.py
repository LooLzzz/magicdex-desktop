import pandas as pd
# import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import Config

from ....BusinessLogic.p_hash import pHash
from ...BaseWidgets.MyQWidget import MyQWidget
from ...BaseWidgets.MyQTableView import MyQTableView
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

        hbox.addSpacerItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.btn_update = QPushButton('Update pHash')
        self.btn_update.clicked.connect(self.onUpdateClicked)
        hbox.addWidget(self.btn_update, alignment=Qt.AlignRight)
        
        self.lbl_rowCount = QLabel('0 Entries')
        hbox.addWidget(self.lbl_rowCount, alignment=Qt.AlignRight)

        self.model = PandasModel(parent=self, df=None, cellValueTooltipEnabled=False)
        self.tableView = MyQTableView(parent=self, model=self.model, contextMenuEnabled=False)
        
        layout.addWidget(self.tableView)

    def filterTextChanged(self, txt):
        # txt = self.text_box.toPlainText()
        self.model.setFilter(txt, columns=['name', 'set', 'collector_number'])
        self.lbl_rowCount.setText(f'{self.model.rowCount()} Entries')
    
    def onUpdateClicked(self, checked:bool):
        worker = pHash.get_pHash_df_qtasync(parent=self, callback=self.getPhashWorkerResults, update=True)
        worker.started.connect(lambda:  ( self.btn_update.setDisabled(True) , self.btn_update.setText('Updating...')  ))
        worker.finished.connect(lambda: ( self.btn_update.setDisabled(False), self.btn_update.setText('Update pHash') ))
        worker.start()

    def onHide(self):
        self.root_window.setMinimumSize(QSize(280, 140))

    def onShow(self):
        self.root_window.setWindowTitle('pHash Viewer')
        self.root_window.resize(1000, 700)
        self.root_window.setMinimumSize(QSize(1000, 700))

        if self.model.dataframe is None:
            pHash \
                .get_pHash_df_qtasync(parent=self, callback=self.getPhashWorkerResults, update=False) \
                .start()

    def getPhashWorkerResults(self, df):
        df['phash'] = df['phash'].apply(lambda x: x.astype('uint8'))
        df['released_at'] = df['released_at'].dt.strftime('%Y-%m-%d')
        df['color_class_(BGR)'] = list(zip(df['b_classes'], df['g_classes'], df['r_classes']))
        df = df.drop(columns=['b_classes','g_classes','r_classes'])
        # df['test'] = pd.Series([ f%2==0 for f in range(len(df))])
        self.model = PandasModel(parent=self, df=df)
        self.tableView.setModel(self.model)
        self.lbl_rowCount.setText(f'{self.model.rowCount()} Entries')
        # self.tableView.model().dataChanged.emit(QModelIndex(), QModelIndex())
