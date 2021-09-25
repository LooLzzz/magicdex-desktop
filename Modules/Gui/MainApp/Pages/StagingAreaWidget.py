import json
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# from config import Config
from ....BusinessLogic import MagicdexApi
# from ...QWorkerThread import QWorkerThread
from ...BaseWidgets.MyQTableView import MyQTableView
from ...BaseWidgets.MyQWidget import MyQWidget
from ...PandasModel import PandasModel

class StagingAreaWidget(MyQWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)

        self.extra_cols = [ 'card_id' ]
        self.view_cols =  [ 'name', 'set_name', 'amount', 'tag', 'condition', 'foil', 'signed', 'altered', 'misprint', 'price' ]
        self.api_cols =   [ 'card_id', 'amount', 'tag', 'condition', 'foil', 'signed', 'altered', 'misprint' ]

        layout = QVBoxLayout()
        self.setLayout(layout)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        df = pd.DataFrame(columns=self.view_cols+self.extra_cols)
        self.model = PandasModel(df=df, priceToolTipEnabled=False, editableColumns=['set_name'])
        self.tableView = MyQTableView(parent=self, model=self.model, columns=self.view_cols, alignment=Qt.AlignCenter, persistentEditorColumns=['condition', 'set_name'])
        self.tableView.selectionModel().setModel(self.model)
        self.tableView.setAlternatingRowColors(True)
        # self.tableView.setFixedHeight(235)
        
        self.model.setHeaderData(self.model.columnNamed('tag'), Qt.Horizontal, "seperated by ';'", Qt.ToolTipRole)
        self.model.setHeaderData(self.model.columnNamed('price'), Qt.Horizontal, "will be updated according to current price", Qt.ToolTipRole)

        self.tableView.setItemDelegateForColumn(self.model.columnNamed('foil'), self.tableView.CheckBoxDelegate(self.tableView))
        self.tableView.setItemDelegateForColumn(self.model.columnNamed('signed'), self.tableView.CheckBoxDelegate(self.tableView))
        self.tableView.setItemDelegateForColumn(self.model.columnNamed('altered'), self.tableView.CheckBoxDelegate(self.tableView))
        self.tableView.setItemDelegateForColumn(self.model.columnNamed('misprint'), self.tableView.CheckBoxDelegate(self.tableView))
        self.tableView.setItemDelegateForColumn(self.model.columnNamed('condition'), self.tableView.ComboBoxDelegate(self.tableView, ['NM', 'LP', 'MP', 'HP', 'DAMAGED']))
        self.tableView.setItemDelegateForColumn(self.model.columnNamed('set_name'), self.tableView.ComboBoxDelegate(self.tableView, []))
        layout.addWidget(self.tableView)

        self.btn_submit = QPushButton('Submit')
        self.btn_submit.clicked.connect(self.onClickSubmit)
        hbox.addWidget(self.btn_submit, alignment=Qt.AlignRight)

    def onHide(self):
        self.root_window.setMinimumSize(QSize(280, 140))

    def onShow(self):
        self.root_window.setWindowTitle('Staging Area')
        self.root_window.resize(875, 835)
        self.root_window.setMinimumSize(QSize(875, 835))

        cardDetectionWidget = self.parent().getPage('cardDetection')
        self_df = self.model.dataframe
        cardDetection_df = cardDetectionWidget.model.dataframe
        
        try:
            self_df = self_df[ self_df['card_id'].isin(cardDetection_df['card_id']) ]
            cardDetection_df = cardDetection_df[ ~ cardDetection_df['card_id'].isin(self_df['card_id']) ]
            
            if not cardDetection_df.empty:
                df = pd.concat([ self_df, cardDetection_df ]) \
                        .fillna({
                            'tag': '',
                            'signed': False,
                            'altered': False,
                            'misprint': False,
                            'condition': 'NM',
                        }) \
                        .reset_index(drop=True) 
                        
                self.tableView.setItemDelegateForColumn(
                    self.model.columnNamed('set_name'),
                    self.tableView.ComboBoxDelegate(self.tableView, cardDetectionWidget.cardSets)
                )
                self.model.setDataFrame(df)
        except KeyError as e:
            pass

    def onClickSubmit(self, checked:bool=...):
        df = self.model \
                .dataframe[self.api_cols] \
                .copy() \
                .rename(columns={'card_id': 'scryfall_id'})
        df['tag']    = df['tag'].apply(lambda x: x.split(';') if x else [])
        df['amount'] = df['amount'].apply(lambda x: f'+{x}') # use '+1' instead of '1'
        cards = df.to_dict('records') # to `List[dict]`
        res = MagicdexApi.update_cards(cards)

        #DEBUG
        try:
            win = self.dialog
            text_edit = self.dialog.text_edit
        except:
            win = self.dialog = QMainWindow()
            text_edit = self.dialog.text_edit = QTextEdit()
            win.layout().addWidget(text_edit)
            text_edit.setReadOnly(True)
        
        text_edit.setText(json.dumps(res, indent=4))
        self.dialog.show()
        #DEBUG
