import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import Config

from ....BusinessLogic import MagicdexApi
from ...BaseWidgets.MyQWidget import MyQWidget

class MainMenu(MyQWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)

        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # hbox = QHBoxLayout()
        # layout.addLayout(hbox)
        
        self.logo_img = QImage(f'{Config.data_path}/logo/Magicdex.png')
        self.logo_lbl = QLabel()
        self.logo_lbl.setPixmap(QPixmap.fromImage(self.logo_img))
        layout.addWidget(self.logo_lbl, alignment=Qt.AlignCenter)

        txt = QLabel('                          \
            <div>                               \
                <h3>                            \
                    Welcome to MagicDex!        \
                </h3>                           \
            </div>                              \
            <div style="text-align:center">     \
                newline 1                       \
            </div>                              \
            <div style="text-align:center">     \
                newline 2                       \
            </div>                              \
        ')
        layout.addWidget(txt, alignment=Qt.AlignCenter)

        # get_btn  = QPushButton(text='get', parent=self, clicked=lambda checked: self.onBtnClicked('get'))
        # by_id_btn  = QPushButton(text='get by id', parent=self, clicked=lambda checked: self.onBtnClicked('by_id'))
        # post_btn = QPushButton(text='post', parent=self, clicked=lambda checked: self.onBtnClicked('post'))
        # hbox.addWidget(get_btn)
        # hbox.addWidget(by_id_btn)
        # hbox.addWidget(post_btn)

        # hbox = QHBoxLayout()
        # layout.addLayout(hbox)
        
        # self.text_field = QTextEdit()
        # hbox.addWidget(self.text_field)

    def resizeEvent(self, event:QResizeEvent):
        logo_img = self.logo_img.scaledToWidth(event.size().width()*0.9, Qt.SmoothTransformation)
        self.logo_lbl.setPixmap(QPixmap.fromImage(logo_img))
        event.accept()

    # def onBtnClicked(self, type):
    #     data = self.text_field.toPlainText()
    #     if not data:
    #         data = '{}'
    #     elif not (data.startswith('{') and data.endswith('}') != '{'):
    #         data = '{' + data.strip('}{') + '}'
    #     try:
    #         data = json.loads(data)
    #     except Exception as e:
    #         pass
        
    #     if type == 'get':
    #         res = MagicdexApi.get(json=data)
    #     elif type == 'post':
    #         res = MagicdexApi.update_cards(data)
    #     elif type == 'by_id':
    #         res = MagicdexApi.get_card_by_id(data)
        
    #     self.text_field.setText(json.dumps(res, indent=4))

    
    def onShow(self):
        self.root_window.setWindowTitle('Main Menu')
        self.root_window.resize(300, 300)
