from collections import OrderedDict
from PyQt5.QtWidgets import QStackedWidget

from . import CustomWidget

class CustomStackedWidget(QStackedWidget):
    def __init__(self, parent, stackPages:CustomWidget):
        QStackedWidget.__init__(self, parent=parent)        
        self.stackPages = OrderedDict([])

        for (pageName, pageClass) in stackPages.items():
            page = pageClass(parent=self, root_window=parent)
            self.stackPages[pageName] = page
            self.addWidget(page)
        
        # self.currentChanged.connect(self.onPageChange)

    def showPage(self, i, invoker=None):
        self.setCurrentIndex(i)
        self.onPageChange(i, invoker=invoker)

    def onPageChange(self, i, invoker=None):
        for (pageName, page) in self.stackPages.items():
            page.onHiddenChange(invoker=invoker, pageName=pageName, i=i)