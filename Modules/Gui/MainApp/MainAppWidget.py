import os, bcrypt
from pymongo import MongoClient
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from ..BaseWidgets import MyStackedWidget
from .Pages import *

class MainAppWidget(MyStackedWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)
        
        self.initPageStack([
            ('mainMenu', MainMenu),
            ('pHash', pHashWidget),
            ('cardDetector', CardDetectorWidget),
            ('stagingArea', StagingAreaWidget),
        ])

        layout = QHBoxLayout(self)
        self.setLayout(layout)

        lbl = QLabel(text='main', parent=self)
        layout.addWidget(lbl)
        self._createMenuBar()

        self.showPage('mainMenu')

    def _createMenuBar(self):
        menuBar = self.root_window.menuBar()
        fileMenu = menuBar.addMenu('&File')
        editMenu = menuBar.addMenu('&Edit')
        helpMenu = menuBar.addMenu('&Help')
        
        fileMenu.addAction('Main Menu', lambda: self.showPage('mainMenu'))
        fileMenu.addAction('Card Detector', lambda: self.showPage('cardDetector'))
        fileMenu.addAction('pHash DataFrame', lambda: self.showPage('pHash'))
        
        editMenu.addAction('Update pHash', lambda: print('TBD')) #TODO implement `update_pHash()` method
        editMenu.addAction('Staging Area', lambda: self.showPage('stagingArea'))

        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+W')
        exitAction.triggered.connect(self.root_window.closeEvent)
        fileMenu.addAction(exitAction)

        helpMenu.addAction('Show Console', self.root_window.console_window.show)