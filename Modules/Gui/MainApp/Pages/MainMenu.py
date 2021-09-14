import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from ....BusinessLogic import MagicdexApi
from ...BaseWidgets.MyQWidget import MyQWidget

class MainMenu(MyQWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)

        layout = QVBoxLayout()
        self.setLayout(layout)
        
        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        get_btn  = QPushButton(text='get', parent=self, clicked=lambda checked: self.onBtnClicked('get'))
        by_id_btn  = QPushButton(text='get by id', parent=self, clicked=lambda checked: self.onBtnClicked('by_id'))
        post_btn = QPushButton(text='post', parent=self, clicked=lambda checked: self.onBtnClicked('post'))
        hbox.addWidget(get_btn)
        hbox.addWidget(by_id_btn)
        hbox.addWidget(post_btn)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)
        
        self.text_field = QTextEdit()
        hbox.addWidget(self.text_field)

    def onBtnClicked(self, type):
        data = self.text_field.toPlainText()
        if not data:
            data = '{}'
        elif not (data.startswith('{') and data.endswith('}') != '{'):
            data = '{' + data.strip('}{') + '}'
        try:
            data = json.loads(data)
        except Exception as e:
            pass
        
        if type == 'get':
            res = MagicdexApi.get(json=data)
        elif type == 'post':
            res = MagicdexApi.update_cards(data)
        elif type == 'by_id':
            res = MagicdexApi.get_card_by_id(data)
        
        self.text_field.setText(json.dumps(res, indent=4))

    
    def onShow(self):
        self.root_window.setWindowTitle('Main Menu')
        self.root_window.resize(300, 300)
