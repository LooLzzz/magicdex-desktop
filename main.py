import sys, traceback
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication

from Modules.Gui import RootWindow
# from Modules.BusinessLogic import *

load_dotenv('dotenv')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RootWindow()
    ex.show()
    ret_val = app.exec_()
    sys.exit()

    # phash_df = pHash.get_pHash_df(update=False)
    # phash_df = pHash.get_pHash_df(update=True)
    # phash_df = pHash.get_pHash_df()
    
    # phash_df = pHash.get_pHash_df(max_workers=1, update=True, flatten_phash=True) #DEBUG
    # phash_df = pHash.get_pHash_df(flatten_phash=True)
    # phash_df = pHash.get_pHash_df(flatten_phash=False)