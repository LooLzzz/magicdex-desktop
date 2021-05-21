import cv2, timeit
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import Config
from ...BaseWidgets import *
from Modules.BusinessLogic.ScryfallApi import fetch_data as fetch
from Modules.BusinessLogic import card_detection as CardDetection, pHash, utils
from Modules.Gui.QWorkerThread import QWorkerThread
from Modules.Gui.PandasModel import PandasModel

class CardDetectionWidget(MyQWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)
        self.isRunning = False
        self.dataframe = None
        self.detectionHelper = DetectionHelper(parent=self)
        self.detectionHelper.results.connect(self.addCardsToTableView)

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

        # self.searchbox = QLineEdit()
        self.searchbox = ScryfallSearchbox()
        self.searchbox.submit.connect(self.searchboxSubmitted)
        self.searchbox.submit.connect(self.searchbox.clear, Qt.QueuedConnection)
        vbox_lower.addWidget(self.searchbox, alignment=Qt.AlignBottom)
        
        self.model = PandasModel()
        self.tableView = MyQTableView(parent=self, model=self.model, columns=['name','set_name','set_id','amount','foil'], alignment=Qt.AlignCenter)
        self.tableView.setSortingEnabled(False)
        self.tableView.hoverIndexChanged.connect(self.onHoverIndexChanged)
        self.tableView.setFixedHeight(252)
        vbox_lower.addWidget(self.tableView, alignment=Qt.AlignBottom)

        self.card_image_label = QLabel()
        self.card_image_label.setFixedSize(200, 280)
        self.setCardImageLabel()
        hbox_lower.addWidget(self.card_image_label, alignment=Qt.AlignRight|Qt.AlignBottom)
    
    def onShow(self):
        self.root_window.setWindowTitle('Card Detection')
        self.root_window.resize(800, 835)

        def _getWorkerResults(dataframe):
            self.dataframe = dataframe
            self.searchbox.setDataFrame(dataframe)

        worker = pHash.get_pHash_df_qtasync(parent=self, callback=_getWorkerResults, update=False)
        worker.start()

    def onHide(self):
        self.stopCamera()

    def setCardImageLabel(self, card=None):
        def _task():
            if card is None:
                pixmap = QPixmap(f'{Config.cards_path}/cardback.jpg', flags=Qt.AvoidDither)\
                        .scaledToWidth(self.card_image_label.width(), Qt.SmoothTransformation)
                self.card_image_label.setPixmap(pixmap)
            else:
                img = fetch.fetch_card_img(card, to_file=True, verbose=False)
                if 'foil' in card and card['foil']:
                    img = utils.add_foil_overlay(img)
                pixmap = QPixmap(QImage(
                    img,
                    img.shape[1],
                    img.shape[0],
                    img.shape[1]*img.shape[2],
                    QImage.Format_BGR888
                )).scaledToWidth(self.card_image_label.width(), Qt.SmoothTransformation)
                self.card_image_label.setPixmap(pixmap)
        
        worker = QWorkerThread(self, _task)
        worker.finished.connect(worker.deleteLater)
        worker.start()
        # worker.exit()
        # worker.quit()

    def searchboxSubmitted(self, card):
        # print(f'got result from searchbox: {card["name"]}')
        self.addCardsToTableView(card)
        self.setCardImageLabel(card)
        
    def addCardsToTableView(self, cards, cards_info=None):
        if not isinstance(cards, pd.DataFrame):
            if isinstance(cards, (list, pd.Series)):
                cards = pd.DataFrame(cards)
            elif isinstance(cards, dict):
                cards = pd.DataFrame([cards])
            else:
                raise ValueError(f'expected {{list | dict | pd.Series | pd.DataFrame}}, got {type(cards)}')

        print('result:', cards[['name','set_id']].values.tolist()) # DEBUG

        card_id = cards['card_id']
        df:pd.DataFrame = self.model.dataframe

        if df is None \
                or df.empty \
                or ('card_id' in df
                        and df[df['card_id'].isin(card_id)].empty):
            cards['amount'] = 1
            cards['foil'] = False
            
            self.model.insertRow(-1, cards)
        else:
            card_rows = df[df['card_id'].isin(card_id)]
            df.loc[card_rows.index, 'amount'] += 1
            self.model.setDataFrame(df)

    def onHoverIndexChanged(self, index:QModelIndex):
        if index.isValid():
            df = self.model.dataframe
            row = index.row()
            card = df.iloc[row]
            self.setCardImageLabel(card)
        else:
            self.setCardImageLabel()

    def openCamera(self):
        if self.isRunning:
            print('Video capture is already running.')
            return
        
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            print('Failed to open camera.')
            return
        
        self.worker = QWorkerThread(self, CardDetection.detect_video,
                                    self.capture, display=False, debug=False, filtering=False,
                                    callback=self.getDetectionResults
                                )
        self.worker.start()
        # CardDetection.detect_video(self.capture, display=False, debug=False, filtering=False, callback=self.getDetectionResults)
        # CardDetection.detect_video(self.capture, display=True, debug=False, filtering=False, callback=self.getDetectionResults)

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
        pixmap = QPixmap(QImage(
            img_result,
            img_result.shape[1],
            img_result.shape[0],
            QImage.Format_BGR888)
        )#.scaledToWidth(self.video_label.width(), Qt.SmoothTransformation)
        self.video_label.setPixmap(pixmap)

        det_cards = pd.DataFrame(det_cards)
        self.detectionHelper(det_cards)

        # if not res.empty:
        #     print('result:', res[['name','set_id']].values.tolist())
        #     self.addCardsToTableView(res)


class DetectionHelper(QObject):
    results = pyqtSignal(pd.DataFrame, pd.DataFrame)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_call_time = None
        self.frame_times = []
        self.fps = 30
        self.cards_buffer = pd.DataFrame(columns=['name','frames_on_screen']) # columns=['frames_on_screen'] + ['name', 'set_id', 'card_id', 'cnt', 'img_warp', 'hash_diff', 'phash']
        self.phash_df = pHash.get_pHash_df(update=False)

    def update_frame_times(self):
        current_call_time = timeit.default_timer()
        if self.last_call_time is not None:
            self.frame_times += [ current_call_time - self.last_call_time ]

        # only keep last N frame times
        keep = 30
        if len(self.frame_times) > keep:
            self.frame_times = self.frame_times[1:keep+1]

        self.fps = 1/np.mean(self.frame_times) if self.frame_times else 30
        self.last_call_time = current_call_time

    def __call__(self, det_cards:pd.DataFrame, time_thresh=1200) -> pd.DataFrame:
        '''
        helper class for calculating which card should be added to the main dataframe
        :param det_cards: cards detected by `detect_video` method
        :param time_thresh: time per card to wait until it is added to the main dataframe or removed from internal buffer, in ms
        :return:
        '''
        self.update_frame_times()
        frame_thresh = int(self.fps * time_thresh / 1000)
        res_info = pd.DataFrame(columns=['card_id', 'name', 'frames_on_screen'])
        plus     = pd.DataFrame(columns=['card_id', 'name', 'frames_on_screen'])
        minus    = pd.DataFrame(columns=['card_id', 'name', 'frames_on_screen'])
        
        try:
            plus = pd.concat([plus,det_cards])
            if not self.cards_buffer.empty:
                if not det_cards.empty:
                    minus = self.cards_buffer[ ~ self.cards_buffer['card_id'].isin(det_cards['card_id']) ].copy()
                else:
                    minus = pd.concat([minus,self.cards_buffer])

            if not plus.empty or not minus.empty:
                if not plus.empty:
                    plus['frames_on_screen']  = 1
                if not minus.empty:
                    minus['frames_on_screen'] = -1

                self.cards_buffer = pd.concat([self.cards_buffer, plus, minus])
                agg_cols = { col:'first' for col in self.cards_buffer if col not in ['frames_on_screen', 'card_id'] }
                agg_cols['frames_on_screen'] = 'sum'
                self.cards_buffer = self.cards_buffer \
                        .groupby('card_id', as_index=False) \
                        .agg(agg_cols) \
                        .reset_index(drop=True)
                
                # cards to remove from buffer
                self.cards_buffer = self.cards_buffer[ self.cards_buffer['frames_on_screen'] > 0 ].copy()

                # cards that got accepted
                res_info = self.cards_buffer[ self.cards_buffer['frames_on_screen'] > frame_thresh ] \
                        .copy() \
                        .reset_index(drop=True)
                if not res_info.empty:
                    cards_to_reset = self.cards_buffer[ self.cards_buffer['card_id'].isin(res_info['card_id']) ]
                    self.cards_buffer.loc[cards_to_reset.index,'frames_on_screen'] = 1

            # print('frame thresh:', frame_thresh)
            # print('plus:', plus[['name', 'frames_on_screen']].values.tolist())
            # print('minus:', minus[['name', 'frames_on_screen']].values.tolist())
            # print('cards buffer:', self.cards_buffer[['name', 'frames_on_screen']].values.tolist())
            # print('---')
            if not res_info.empty:
                res = self.phash_df[ self.phash_df['card_id'].isin(res_info['card_id']) ]
                self.results.emit(res, res_info)
        except Exception as e:
            print(e)
