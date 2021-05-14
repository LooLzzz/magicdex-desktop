import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from . import LoginWidget, ConsoleWindow
from . import MainAppWidget

class RootWindow(QMainWindow):
    closeSignal = pyqtSignal(QEvent)

    def __init__(self):
        super().__init__()
        
        self.console_window = ConsoleWindow()
        self.console_window.setGeometry(800, 275, 800, 220)
        self.closeSignal.connect(self.console_window.close)
        
        # #DEBUG
        # mainAppWidget = MainAppWidget(self, self) 
        # mainAppWidget.showPage('cardDetection')
        # self.setCentralWidget(mainAppWidget)
        # #DEBUG

        loginWidget = LoginWidget(self, self)
        self.setCentralWidget(loginWidget)
        self.setGeometry(500, 125, 10, 10)
        loginWidget.onShow()

    def closeEvent(self, event):
        try:
            self.closeSignal.emit(event)
            event.accept()
        except AttributeError:
            qApp.quit()