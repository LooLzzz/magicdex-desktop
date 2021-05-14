import cv2
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import Config
from ...BaseWidgets import MyQWidget
from Modules.BusinessLogic import card_detection as CardDetection
from Modules.Gui.QWorkerThread import QWorkerThread
from Modules.Gui.PandasModel import PandasModel

class CardDetectionWidget(MyQWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)
        self.isRunning = False

        vbox_main = QVBoxLayout()
        vbox_lower = QVBoxLayout()
        hbox_upper = QHBoxLayout()
        hbox_lower = QHBoxLayout()
        self.setLayout(vbox_main)
        
        # start/stop buttons
        btnStart = QPushButton("Open camera")
        btnStart.clicked.connect(self.openCamera)
        btnStop = QPushButton("Stop camera")
        btnStop.clicked.connect(self.stopCamera)
        
        hbox_upper.addWidget(btnStart)
        hbox_upper.addWidget(btnStop)
        vbox_main.addLayout(hbox_upper)
        
        # image label
        self.video_label = QLabel()
        self.video_label.resize(640, 640)
        vbox_main.addWidget(self.video_label, alignment=Qt.AlignCenter)

        vbox_main.addLayout(hbox_lower)
        hbox_lower.addLayout(vbox_lower)

        self.searchbox = QTextEdit()
        self.searchbox.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.searchbox.setLineWrapMode(QTextEdit.NoWrap)
        self.searchbox.setFixedHeight(25)
        self.searchbox.textChanged.connect(self.searchboxTextChanged)
        vbox_lower.addWidget(self.searchbox, alignment=Qt.AlignBottom)
        
        self.model = PandasModel(df=pd.DataFrame(columns=['name','set','amount','foil']))
        self.tableView = QTableView()
        self.tableView.setSortingEnabled(True)
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) 
        self.tableView.setShowGrid(False) 
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setModel(self.model)
        vbox_lower.addWidget(self.tableView, alignment=Qt.AlignBottom)

        self.card_image_label = QLabel()
        self.card_image_label.setFixedSize(200, 280)
        self.cardback_pixmap = QPixmap(f'{Config.cards_path}/cardback.jpg', flags=Qt.AvoidDither).scaledToWidth(200)
        self.card_image_label.setPixmap(self.cardback_pixmap)
        hbox_lower.addWidget(self.card_image_label, alignment=Qt.AlignRight|Qt.AlignBottom)
    
    def onShow(self):
        self.root_window.setWindowTitle('Card Detection')
        self.root_window.resize(800, 835)

    def onHide(self):
        self.stopCamera()

    def searchboxTextChanged(self):
        pass

    def openCamera(self):
        if self.isRunning:
            print('Video capture is already running.')
            return
        
        self.capture = cv2.VideoCapture(0)        
        if not self.capture.isOpened():
            print('Failed to open camera.')
        
        self.worker = QWorkerThread(self, CardDetection.detect_video,
                                        self.capture, display=False, debug=False, filtering=False, callback=self.getDetectionResults)
        self.worker.start()
        # CardDetection.detect_video(self.capture, display=False, debug=False, filtering=False, callback=self.getDetectionResults)

        self.isRunning = True

    def stopCamera(self):
        if self.isRunning:
            if hasattr(self, 'worker'):
                self.worker.terminate()
            if hasattr(self, 'capture'):
                self.capture.release()
            self.video_label.clear()
            self.isRunning = False
            print() # print a new line

    def getDetectionResults(self, det_cards, img_result):
        img_result = cv2.cvtColor(img_result, cv2.COLOR_BGR2RGB)
        image = QImage(img_result, img_result.shape[1], img_result.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self.video_label.setPixmap(pixmap)

        names = [ d['name'] for d in det_cards if 'name' in d ]
        if len(names) == 0:
            print('det_cards: []\r', end='')
        else:
            print(f'det_cards: {names}')