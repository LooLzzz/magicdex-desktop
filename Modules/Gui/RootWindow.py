import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from ..BusinessLogic import MagicdexApi
from .MainApp.ConsoleWindow import ConsoleWindow
from .MainApp.MainAppWidget import MainAppWidget

class RootWindow(QMainWindow):
    closeSignal = pyqtSignal(QEvent)

    def __init__(self):
        super().__init__()
        # self.setMinimumSize(280, 160)
        # self.setMaximumSize(2000, 2000)
        self.setGeometry(500, 125, 10, 10) # x, y, w, h

        self.console_window = ConsoleWindow()
        self.console_window.setGeometry(800, 275, 800, 220)
        self.closeSignal.connect(self.console_window.close)
        
        self.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint)

        mainAppWidget = MainAppWidget(self, self)
        self.setCentralWidget(mainAppWidget)
        
        username = MagicdexApi.check_jwt()        
        if username:
            mainAppWidget.showPage('mainMenu')
            self.statusBar().showMessage(f'Welcome back {username}', 5000)
        else:
            mainAppWidget.showPage('login')
            self.statusBar().showMessage('')

    def closeEvent(self, event):
        try:
            self.closeSignal.emit(event)
            event.accept()
        except AttributeError:
            qApp.quit()
