from PyQt5.QtWidgets import QWidget

class CustomWidget(QWidget):
    def __init__(self, parent, root_window):
        QWidget.__init__(self, parent=parent)
        self.root_window = root_window
    
    def onHiddenChange(self, invoker, *args, **kwargs):
        pass