from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from Modules.BusinessLogic import pHash
from ..BaseWidgets import MyQTableView
from ..PandasModel import PandasModel

CompleterRole = Qt.UserRole + 1

class ScryfallSearchbox(QLineEdit):
    submit = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText('Search cards..')
        
        self.phash_df = pHash.get_pHash_df(update=False) \
                .drop_duplicates(subset='name', keep='first') \
                .sort_values(by='name')
        self.model = PandasModel(df=self.phash_df)

        completer = MyCompleter(self.model, column=3, parent=self)
        self.setCompleter(completer)

        # self.textEdited.connect(self.onTextEdited)

    # def setCompleter(self, completer):
    #     self._completer = completer

    def keyPressEvent(self, event:QKeyEvent):
        key = event.key()
        if key == Qt.Key_Enter or key == Qt.Key_Return:
            # self.submit.emit(self.text())
            df = self.model.dataframe
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
    def __init__(self, pandasModel, column, parent=None):
        super().__init__(parent)
        proxy = CompleterProxyModel(column)
        proxy.setSourceModel(pandasModel)
        self.setModel(proxy)
        # self.setModel(pandasModel)

        self.setCompletionColumn(column)
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