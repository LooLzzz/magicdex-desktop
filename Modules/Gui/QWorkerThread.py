from PyQt5.QtCore import *

class QWorkerThread(QThread):
    results = pyqtSignal(object)
    
    def __init__(self, parent, task, *args, **kwargs,):
        super().__init__(parent)
        self.task = task
        self.args = args
        self.kwargs = kwargs

    def run(self):
        res = self.task(*self.args, **self.kwargs)
        self.results.emit(res)
