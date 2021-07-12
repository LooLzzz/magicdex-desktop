import sys #, cgitb
# import asyncio
# from qasync import QEventLoop
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication

from Modules import RootWindow

load_dotenv('.env')

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)

if __name__ == '__main__':
    # cgitb.enable(format='text')
    sys.excepthook = except_hook

    ## sequential ##
    app = QApplication(sys.argv)
    ex = RootWindow()
    ex.show()
    app.exec_()
    sys.exit()
    
    
    # ## async ##
    # app = QApplication(sys.argv)
    # loop = QEventLoop(app)
    # asyncio.set_event_loop(loop)
    # ex = RootWindow()
    # ex.show()
    # loop.run_forever()
    