from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from ...BaseWidgets.MyQWidget import MyQWidget

class StagingAreaWidget(MyQWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)

    def onShow(self):
        self.root_window.setWindowTitle('Staging Area')