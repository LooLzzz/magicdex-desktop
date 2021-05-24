# from collections import OrderedDict
from PyQt5.QtWidgets import *

from .MyQWidget import MyQWidget

class MyStackedQWidget(QStackedWidget):
    def __init__(self, parent, root_window, pageStack:MyQWidget=None):
        super().__init__(parent=parent)
        self.prevIndex = -1
        self.root_window = root_window
        self.currentChanged.connect(self.onPageChange)
        
        if pageStack is not None:
            self.initPageStack(pageStack)

    def initPageStack(self, pageStack):
        self.pageStack = []
        for (_pageName,_pageClass) in pageStack:
            _pageWidget = _pageClass(parent=self, root_window=self.root_window)
            self.pageStack += [ (_pageName, _pageWidget) ]
            self.addWidget(_pageWidget)
        # self.setCurrentIndex(0)

    def showPage(self, pageName):
        # self.prevIndex = self.currentIndex()
        for (i, (_pageName,_pageWidget)) in enumerate(self.pageStack):
            if _pageName == pageName:
                self.setCurrentIndex(i)
                break

    def getPage(self, pageName):
        for (_pageName,_pageWidget) in self.pageStack:
            if _pageName == pageName:
                return _pageWidget

    def onPageChange(self, i):        
        _,prevPage = self.pageStack[self.prevIndex]
        prevPage.onHide()
        
        _,currPage = self.pageStack[i]
        currPage.onShow()
        
        self.prevIndex = self.currentIndex()
    
    def onShow(self):
        pass

    def onHide(self):
        pass