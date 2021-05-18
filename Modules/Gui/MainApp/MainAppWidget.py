import os, bcrypt
from pymongo import MongoClient
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from ..BaseWidgets import MyStackedQWidget, MyQWidget
from .Pages import *

class MainAppWidget(MyStackedQWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)
        
        # creates `self.pageStack:list` internally
        self.initPageStack([
            ('mainMenu', MainMenu),
            ('pHash', pHashWidget),
            ('cardDetection', CardDetectionWidget),
            ('stagingArea', StagingAreaWidget),
        ])

        self._createMenuBar()
        self.showPage('mainMenu')

    def _createMenuBar(self):
        menuBar = self.root_window.menuBar()
        fileMenu = menuBar.addMenu('&File')
        editMenu = menuBar.addMenu('&Edit')
        helpMenu = menuBar.addMenu('&Help')
        
        fileMenu.addAction('Main Menu', lambda: self.showPage('mainMenu'))
        fileMenu.addAction('Card Detection', lambda: self.showPage('cardDetection'))
        fileMenu.addAction('pHash DataFrame', lambda: self.showPage('pHash'))
        
        # editMenu.addAction('Update pHash', lambda: self.getPage('pHash').load_phash(True))
        editMenu.addAction('Update pHash', self._update_phash)
        editMenu.addAction('Staging Area', lambda: self.showPage('stagingArea'))

        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+W')
        exitAction.triggered.connect(self.root_window.close)
        fileMenu.addAction(exitAction)

        helpMenu.addAction('Show Console', self.root_window.console_window.show)

    def _update_phash(self):
        from Modules.BusinessLogic import pHash
        worker = pHash.get_pHash_df_qtasync(parent=self, callback=None, update=True)
        worker.start()