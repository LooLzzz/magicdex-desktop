from PyQt5.QtWidgets import *

class MyQWidget(QWidget):
    def __init__(self, parent, root_window):
        super().__init__(parent=parent)
        self.root_window = root_window
    
    def onShow(self, *args, **kwargs):
        pass

    def onHide(self, *args, **kwargs):
        pass