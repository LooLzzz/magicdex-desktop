import sys
# import asyncio
# from qasync import QEventLoop
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication

from Modules.Gui import RootWindow
# from Modules.BusinessLogic import *

load_dotenv('dotenv')

if __name__ == '__main__':
    ## sequential ##
    try:
        app = QApplication(sys.argv)
        ex = RootWindow()
        ex.show()
        app.exec_()
    except BaseException as e:
        print(e)
    finally:
        sys.exit()
    
    
    # ## async ##
    # app = QApplication(sys.argv)
    # loop = QEventLoop(app)
    # asyncio.set_event_loop(loop)
    # ex = RootWindow()
    # ex.show()
    # loop.run_forever()
    