import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from .Login.LoginWidget import LoginWidget
from .MainApp.ConsoleWindow import ConsoleWindow
from .MainApp.MainAppWidget import MainAppWidget

class RootWindow(QMainWindow):
    closeSignal = pyqtSignal(QEvent)

    def __init__(self):
        super().__init__()
        self.setGeometry(500, 125, 10, 10) # x, y, w, h
        
        self.console_window = ConsoleWindow()
        self.console_window.setGeometry(800, 275, 800, 220)
        self.closeSignal.connect(self.console_window.close)
        
        #DEBUG
        mainAppWidget = MainAppWidget(self, self) 
        mainAppWidget.showPage('mainMenu')
        # mainAppWidget.showPage('cardDetection')
        # mainAppWidget.showPage('pHash')
        self.setCentralWidget(mainAppWidget)
        #DEBUG

        # loginWidget = LoginWidget(self, self)
        # self.setCentralWidget(loginWidget)
        # loginWidget.onShow()

    def closeEvent(self, event):
        try:
            self.closeSignal.emit(event)
            event.accept()
        except AttributeError:
            qApp.quit()