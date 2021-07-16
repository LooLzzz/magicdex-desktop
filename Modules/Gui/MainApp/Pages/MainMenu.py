from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from ...BaseWidgets.MyQWidget import MyQWidget

class MainMenu(MyQWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)

        layout = QHBoxLayout()
        self.setLayout(layout)

        lbl = QLabel(text='main', parent=self)
        layout.addWidget(lbl)
    
    def onShow(self):
        self.root_window.setWindowTitle('Main Menu')
        self.root_window.resize(300, 300)
