import sys, os, cv2
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from card_detection import detect_video
from . import CustomWidget


class CardDetectorWidget(CustomWidget):
    def __init__(self, parent, root_window):
        CustomWidget.__init__(self, parent, root_window)

        # Create a layout.
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.isRunning = False

        # button layout
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        btnCamera = QPushButton("Open camera")
        btnCamera.clicked.connect(self.openCamera)
        button_layout.addWidget(btnCamera)

        btnCamera = QPushButton("Stop camera")
        btnCamera.clicked.connect(self.stopCamera)
        button_layout.addWidget(btnCamera)

        # Add an image label
        self.image_label = QLabel()
        self.image_label.resize(640, 640)
        layout.addWidget(self.image_label)

        # Add a text area
        # self.results = QTextEdit()
        # self.readBarcode()
        # layout.addWidget(self.results)

    def onHiddenChange(self, invoker, *args, **kwargs):
        if self.isHidden():
            self.stopCamera()
        else:
            self.root_window.resize(800, 800)

    def openCamera(self):
        try:
            if self.isRunning:
                print('Video capture is already running.')
                return
        except AttributeError as e:
            pass
        
        self.capture = cv2.VideoCapture(0)        

        if not self.capture.isOpened():
            print('Failed to open camera.')
        
        self.worker = self._WorkerThread(parent=self, capture=self.capture)
        self.worker.results.connect(self.getWorkerResults)
        self.worker.start()

        self.isRunning = True

    def stopCamera(self):
        if self.isRunning:
            if hasattr(self, 'worker'):
                self.worker.terminate()
            if hasattr(self, 'capture'):
                self.capture.release()
            self.image_label.clear()
            self.isRunning = False
            print() # print a new line

    def getWorkerResults(self, img_result, det_cards):
        img_result = cv2.cvtColor(img_result, cv2.COLOR_BGR2RGB)
        image = QImage(img_result, img_result.shape[1], img_result.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self.image_label.setPixmap(pixmap)

        names = [ d['name'] for d in det_cards if 'name' in d ]
        if len(names) == 0:
            print('det_cards: []\r', end='')
        else:
            print(f'det_cards: {names}')


    # def nextFrameSlot(self):
    #     rval, frame = self.capture.read()
    #     frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #     image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
    #     pixmap = QPixmap.fromImage(image)
    #     self.image_label.setPixmap(pixmap)

    #     results = []
    #     out = ''
    #     index = 0
    #     for result in results:
    #         out += "Index: " + str(index) + "\n"
    #         out += "Barcode format: " + result[0] + '\n'
    #         out += "Barcode value: " + result[1] + '\n'
    #         out += '-----------------------------------\n'
    #         index += 1

    #     self.results.setText(out)
    
    
    class _WorkerThread(QThread):
        results = pyqtSignal(np.ndarray, list)
        
        def __init__(self, parent, capture):
            super().__init__(parent)
            self.capture = capture

        def run(self):
            detect_video(self.capture, display=False, debug=False, filtering=False, callback=self.detect_video_callback)
        
        # @pyqtSlot(np.ndarray, list)
        def detect_video_callback(self, img_result, det_cards):
            self.results.emit(img_result, det_cards)
            # return (img_result, det_cards)
        