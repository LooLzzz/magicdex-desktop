import pandas as pd
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ...BusinessLogic import pHash
from ..BaseWidgets import MyQTableView
from ..PandasModel import PandasModel

CompleterRole = Qt.UserRole + 1

class ScryfallSearchbox(QLineEdit):
    submit = pyqtSignal(object)

    def __init__(self, parent=None, dataframe=None):
        super().__init__(parent)
        self.setPlaceholderText('Search cards..')
        
        if dataframe is not None:
            self.setDataFrame(dataframe)

    # def setCompleter(self, completer):
    #     self._completer = completer

    def setDataFrame(self, dataframe:pd.DataFrame):
        # no transform cards, no dupes
        self.dataframe = dataframe \
                [ ~ dataframe['name'].str.contains('\(back\)') ] \
                .sort_values(by=['name','released_at'], ascending=[True,False]) \
                .drop_duplicates('name', keep='first') \
                .reset_index(drop=True)
        
        # all cards (with dupes), not including back side of transform cards
        self.all_cards = dataframe[ ~ dataframe['name'].str.contains('\(back\)') ]
        
        self.model = PandasModel(parent=self, df=self.dataframe)
        completer = MyCompleter(self.model, column=0, parent=self)
        
        self.setCompleter(completer)
        # self.textEdited.connect(self.onTextEdited)

    def keyPressEvent(self, event:QKeyEvent):
        key = event.key()
        if key == Qt.Key_Enter or key == Qt.Key_Return:
            # self.submit.emit(self.text())
            df = self.dataframe
            rows = df[ df['name'].str.lower() == self.text().lower() ]
            if len(rows) > 0:
                val = rows.iloc[0].to_dict()
                self.submit.emit(val)
                # self.setText('')
                # self.update()
        super().keyPressEvent(event)
    
    def onTextEdited(self, txt):
        '''
        start completion after 3 characters
        '''
        txt_len = len(txt)
        if txt_len < 3:
            super().setCompleter(None)
        elif len(txt) >= 3:
            completer = self.completer()
            if completer != self._completer:
                super().setCompleter(self._completer)


class MyCompleter(QCompleter):
    def __init__(self, model:PandasModel, column, parent=None):
        super().__init__(parent)
        proxy = CompleterProxyModel(column)
        proxy.setSourceModel(model)
        self.setModel(proxy)
        # self.setModel(pandasModel)

        if isinstance(column, int):
            self.setCompletionColumn(column)
        else:
            self.setCompletionColumn(model.columnNamed(column))

        self.setCompletionRole(CompleterRole)
        # self.setFilterMode(Qt.MatchContains)
        self.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.setCaseSensitivity(False)
        
        self.popup().setUniformItemSizes(True)
        self.popup().setLayoutMode(QListView.Batched)

        # table_view = MyQTableView(columns=[column,1])
        # table_view.horizontalHeader().hide()
        # self.setPopup(table_view)

        self.activated.connect(self.onActivated)
    
    def onActivated(self, txt):
        pass
        # df = self.model().sourceModel().dataframe
        # rows = df[ df['name'] == txt ]
        # if len(rows) > 0:
        #     val = rows.iloc[0].to_dict()
        #     self.parent().submit.emit(val)

class CompleterProxyModel(QIdentityProxyModel):
    def __init__(self, column, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._column = column

    def data(self, index, role):
        if role == CompleterRole:
            return str(self.sibling(index.row(), self._column, index.parent()).data())
                    # .replace(',','') \
                    # .replace('"','') \
                    # .replace("'",'')
        return super().data(index, role)