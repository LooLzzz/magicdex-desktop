from PyQt5.QtWidgets import *

from p_hash import pHash
from . import CustomWidget
from .LoginWidget import LoginWidget

class MainWidget(CustomWidget):
    def __init__(self, parent, root_window):
        CustomWidget.__init__(self, parent, root_window)
        # self._createMenuBar()
        
        layout = QHBoxLayout(self)
        self.setLayout(layout)

        lbl = QLabel(text='main', parent=self)
        layout.addWidget(lbl)

    def _createMenuBar(self):
        menuBar = self.root_window.menuBar()
        fileMenu = menuBar.addMenu('&File')
        editMenu = menuBar.addMenu('&Edit')
        helpMenu = menuBar.addMenu('&Help')
        
        fileMenu.addAction('Main Page', lambda: self.root_window.showPage('main'))
        fileMenu.addAction('pHash DataFrame', lambda: self.root_window.showPage('phash'))
        fileMenu.addAction('Card Detector', lambda: self.root_window.showPage('cardDetector'))
        
        editMenu.addAction('Update pHash', self.update_pash)
        editMenu.addAction('Staging Area', lambda: self.root_window.showPage('stagingArea'))

        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+W')
        exitAction.triggered.connect(self.root_window.closeEvent)
        fileMenu.addAction(exitAction)

        helpMenu.addAction('Show Console', self.root_window.console_window.show)
        
    def onHiddenChange(self, invoker, *args, **kwargs):
        if self.isHidden():
            pass
        else:
            if isinstance(invoker, LoginWidget):
                self._createMenuBar()
                # self.root_window.console_window.show()
            self.root_window.setWindowTitle('Card Detector')
            self.root_window.resize(300, 300)

    def update_pash(self):
        self.root_window.stack.stackPages['phash'].update_phash()