import sys
from tqdm import tqdm
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from . import CustomWidget

class StagingAreaWidget(CustomWidget):
    def __init__(self, parent, root_window):
        CustomWidget.__init__(self, parent, root_window)

    def onHiddenChange(self, invoker, *args, **kwargs):
        if self.isHidden():
            pass
        else:
            self.root_window.setWindowTitle('Staging Area')
            self.root_window.resize(300, 300)

            self.thread = QThread()
            self.worker = self._Worker()
            self.worker.moveToThread(self.thread)
            
            self.thread.started.connect(self.worker.run)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            
            self.thread.start()
    
    class _Worker(QObject):
        finished = pyqtSignal()
        
        def __init__(self):
            QObject.__init__(self)

        def run(self):
            for _i in tqdm(range(10000000), ncols=75, ascii=False, file=sys.stdout):
                pass
            self.finished.emit()