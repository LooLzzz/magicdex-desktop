import sys
from collections import OrderedDict
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from dotenv import load_dotenv

sys.path.insert(1, '..')
sys.path.insert(1, '.')

from Widgets import *
from ConsoleWindow import ConsoleWindow

load_dotenv('dotenv')

class RootWidget(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.console_window = ConsoleWindow(parent=self)
        self.console_window.setGeometry(1000, 275, 550, 200)

        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)
        self.setGeometry(350, 150, 10, 10)
        # self.setFixedSize(10, 10)

        stackPages = OrderedDict([
            ('login', LoginWidget),
            ('main', MainWidget),
            ('phash', pHashWidget),
            ('cardDetector', CardDetectorWidget),
            ('stagingArea', StagingAreaWidget),
        ])
        self.stack = CustomStackedWidget(parent=self, stackPages=stackPages) 
        self.setCentralWidget(self.stack)

        self.statusBar().showMessage('')
        self.showPage('login', self)
    
    def closeEvent(self, event):
        msg = "Close the app?"
        reply = QMessageBox.question(self, 'Quit', msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                event.accept()
                self.stack.stackPages['cardDetector'].stopCamera()
            except AttributeError:
                qApp.quit()
        else:
            event.ignore()
    
    def showPage(self, value, invoker=None):
        if isinstance(value, str):
            i = list(self.stack.stackPages).index(value)
        elif isinstance(value, int):
            i = value
        
        self.stack.showPage(i, invoker=invoker)
               
	
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RootWidget()
    ex.show()
    sys.exit(app.exec_())
