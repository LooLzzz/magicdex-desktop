import cv2, timeit, sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import Config
from ....BusinessLogic.ScryfallApi import scryfall_client as scryfall
from ....BusinessLogic.ScryfallApi import fetch_data as fetch
from ....BusinessLogic import card_detection as CardDetection, utils
from ....BusinessLogic.p_hash import pHash
from ...QWorkerThread import QWorkerThread
from ...BaseWidgets.MyQTableView import MyQTableView
from ...BaseWidgets.MyQWidget import MyQWidget
from ...BaseWidgets.ScryfallSearchbox import ScryfallSearchbox
from ...PandasModel import PandasModel


class CardDetectionWidget(MyQWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)
        self.isRunning = False
        self.dataframe = None
        self.rotation_flag = False
        self.image_worker = None
        self.detectionHelper = DetectionHelper(parent=self)
        self.detectionHelper.results.connect(self.addCardsToTableView)
        self.cardSets = {}  # dict of all cards in the tableview, containing a dict of all sets in which each of them appear
                            # the key is the card name, the value is a df of that card in each set it appears
                            # { 'fireball': fireball_df, 'shock': shock_df, ... }

        vbox_main = QVBoxLayout()
        vbox_lower = QVBoxLayout()
        hbox_upper = QHBoxLayout()
        hbox_lower = QHBoxLayout()
        self.setLayout(vbox_main)
        
        # start/stop buttons
        btnStart = QPushButton("Open camera")
        btnStart.clicked.connect(self.openCamera)
        btnStop = QPushButton("Close camera")
        btnStop.clicked.connect(self.stopCamera)
        
        hbox_upper.addWidget(btnStart)
        hbox_upper.addWidget(btnStop)
        vbox_main.addLayout(hbox_upper)
        
        # image label
        self.video_label = QLabel()
        self.video_label.resize(640, 480)
        vbox_main.addWidget(self.video_label, alignment=Qt.AlignCenter)

        vbox_main.addLayout(hbox_lower)
        hbox_lower.addLayout(vbox_lower)

        # self.searchbox = QLineEdit()
        self.searchbox = ScryfallSearchbox()
        self.searchbox.submit.connect(self.searchboxSubmitted)
        self.searchbox.submit.connect(self.searchbox.clear, Qt.QueuedConnection)
        vbox_lower.addWidget(self.searchbox, alignment=Qt.AlignBottom)
        
        _cols = ['collector_number','name','set_name','amount','foil','price']
        self.model = PandasModel(df=pd.DataFrame(columns=_cols), priceToolTipEnabled=True)
        self.tableView = MyQTableView(parent=self, model=self.model, columns=_cols, alignment=Qt.AlignCenter)
        self.tableView.selectionModel().setModel(self.model)
        self.tableView.setAlternatingRowColors(False)
        self.tableView.setSortingEnabled(False)
        self.tableView.hoverIndexChanged.connect(self.onHoverIndexChanged)
        self.tableView.currentChangedSignal.connect(self.onCurrentChanged)
        # self.tableView.selectionModel().currentChanged.connect(self.onCurrentChanged)
        self.tableView.setFixedHeight(235)

        self.model.setHeaderData(self.model.columnNamed('price'), Qt.Horizontal, "will be updated according to current price", Qt.ToolTipRole)
        self.tableView.contextMenuCustomActions = [
            [ 'Change Set', [] ],
            None, # Seperator
        ]

        self.tableView.setItemDelegateForColumn(self.model.columnNamed('foil'), self.tableView.CheckBoxDelegate())
        # self.tableView.setItemDelegateForColumn(self.model.columnNamed('amount'), self.tableView.ValidatedItemDelegate())
        
        vbox_lower.addWidget(self.tableView, alignment=Qt.AlignBottom)

        self.card_image_label = QLabel()
        self.card_image_label.setFixedSize(200, 280)
        self.setCardImageLabel()
        hbox_lower.addWidget(self.card_image_label, alignment=Qt.AlignRight|Qt.AlignBottom)
        
        btn_staging_area = QPushButton("Goto\nStaging Area")
        btn_staging_area.clicked.connect(lambda: self.parent().showPage('stagingArea'))
        hbox_lower.addWidget(btn_staging_area, alignment=Qt.AlignRight)

        self.rotate_frame = QFrame(parent=self.video_label)
        self.rotate_frame.setGeometry(595, -5, 50, 50)
        vbox = QVBoxLayout()
        self.rotate_btn = QPushButton('⭮')
        font = self.rotate_btn.font()
        font.setBold(True)
        font.setPixelSize(25)
        self.rotate_btn.setFont(font)
        self.rotate_btn.clicked.connect(self.onRotateBtnClicked)
        self.rotate_frame.setHidden(True)
        vbox.addWidget(self.rotate_btn)
        self.rotate_frame.setLayout(vbox)

    def onShow(self):
        self.root_window.setWindowTitle('Card Detection')
        self.root_window.resize(875, 835)
        self.root_window.setMinimumSize(QSize(875, 835))

        def _getWorkerResults(dataframe):
            self.dataframe = dataframe
            self.searchbox.setDataFrame(dataframe)

        worker = pHash.get_pHash_df_qtasync(parent=self, callback=_getWorkerResults, update=False)
        worker.start()

    def onHide(self):
        self.root_window.setMinimumSize(QSize(280, 140))
        self.stopCamera()

    def updateCardSets(self, new_cards):       
        '''asynchronically update `self.cardSets` to contain all versions of the current cards in the tableview'''
        def _task():
            res = {}
            for card in new_cards:
                try:
                    card_res = scryfall.get_card_sets(name=card)
                    card_res['amount'] = 1
                    card_res['price'] = None
                    res[card] = card_res
                except:
                    res[card] = None
            return res
        
        def _results(res):
            self.cardSets.update(res)

        # _results(_task())
        worker = QWorkerThread(self, _task)
        worker.results.connect(_results)
        worker.finished.connect(worker.deleteLater)
        worker.start()

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
        
        # if self.image_worker and self.image_worker.isRunning():
        #     self.image_worker.deleteLater()

        self.image_worker = QWorkerThread(self, _task)
        self.image_worker.finished.connect(self.image_worker.deleteLater)
        self.image_worker.start()
        # _task()

    def onRotateBtnClicked(self, _checked):
        self.rotation_flag = not self.rotation_flag
        
        if self.cardDetectionWorker.isRunning():
            self.cardDetectionWorker.terminate()

        self.cardDetectionWorker = QWorkerThread(self, CardDetection.detect_video,
                                    capture=self.capture, display=False, debug=False, filtering=False,
                                    callback=self.getDetectionResults, rotation_flag=self.rotation_flag
                                )
        self.cardDetectionWorker.start()

    def searchboxSubmitted(self, card):
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

        # cards_id = cards['card_id']
        df = self.model.dataframe

        if df is None:
            df = pd.DataFrame(columns=['card_id'])
        elif 'card_id' not in df:
            df['card_id'] = None
        
        new_cards = cards[ ~ cards['card_id'].isin(df['card_id']) ]
        old_cards = cards[ cards['card_id'].isin(df['card_id']) ]

        if not new_cards.empty:
            # cards THAT ARE NOT present in the tableview           
            new_cards['amount'] = 1
            new_cards['foil'] = False
            new_cards['price'] = None

            self.updateCardSets(new_cards['name'])
            self.model.insertRow(-1, new_cards)
            select_rows = [self.model.rowCount()-1]
            df = self.model.dataframe
        
        if not old_cards.empty:
            # card THAT ARE ALREADY present in the tableview
            cards_row = df[ df['card_id'].isin(old_cards['card_id']) ]
            df.loc[cards_row.index, 'amount'] += 1
            self.model.setDataFrame(df)
            select_rows = cards_row.index.tolist()
        
        # self.tableView.clearSelection()
        self.tableView.selectionModel().clearSelection()

        indexes = [ self.tableView.model().index(i, 0) for i in select_rows ]
        mode = QItemSelectionModel.Select | QItemSelectionModel.Rows
        for index in indexes:
            self.tableView.selectionModel().select(index, mode)

        # self.setSelectionMode(QAbstractItemView.MultiSelection)
        # for i in select_rows:
        #     self.tableView.selectRow(i)
        # self.setSelectionMode(QAbstractItemView.SingleSelection)

        self.setCardImageLabel(cards.iloc[-1])
        idx = self.tableView.model().index( min(select_rows), 0)
        # for some reason you need to call `scrollTo()` twice for it to work 🤷‍♂️
        self.tableView.scrollTo(idx)
        self.tableView.scrollTo(idx)

    def onCurrentChanged(self, current:QModelIndex, previous:QModelIndex):
        # the context needs to updated for each different card when right clicking on a list item
        if current.isValid():
            row = current.row()
            # col = current.column()

            card = self.model.dataframe.iloc[row]
            card_name = card['name']

            actions = []
            if card_name in self.cardSets:
                cards_df = self.cardSets[card_name]
                if cards_df is not None:
                    # card_sets = card_sets['set_name'].values

                    for i,card in cards_df.iterrows():
                        actions += [ (
                            f'{card["set_name"]} - {card["collector_number"]}',
                            lambda row=row, card=card: self.replaceRow(row=row, card=card)
                        ) ]
                    
            # update `contextMenuActions['Change Set'][actions]`
            self.tableView.contextMenuCustomActions[0][1] = actions
            # print(f'updated context menu for {{row:{row}, name:"{card_name}"}}') # DEBUG

    def replaceRow(self, row, card):
        _cols = [
            ['collector_number', 'name', 'set_name', 'amount', 'foil', 'price', 'card_id', 'set_id', 'released_at', 'image_url'],
            ['phash', 'b_classes', 'g_classes', 'r_classes']
        ]
        df = self.model.dataframe
        # card['image_url'] = card['image_uris']['border_crop']
        card['image_url'] = card['image_uris']['normal']
        card['amount'] = df.loc[row, 'amount']
        card['foil'] = df.loc[row, 'foil']
        
        card = card[_cols[0]]
        for col in _cols[1]:
            card[col] = None
        
        df.iloc[row] = card
        self.model.setDataFrame(df)
        self.setCardImageLabel(card)

    def onHoverIndexChanged(self, index:QModelIndex):
        self.currentHoveringIndex = index

        if index.isValid():
            df = self.model.dataframe
            row = index.row()
            card = df.iloc[row]
            self.setCardImageLabel(card)
        else:
            self.setCardImageLabel(None)

    def openCamera(self):
        if self.isRunning:
            print('Video capture is already running.')
            return
        
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            print('Failed to open camera.')
            return
        
        self.rotate_frame.setHidden(False)
        self.cardDetectionWorker = QWorkerThread(self, CardDetection.detect_video,
                                    capture=self.capture, display=False, debug=False, filtering=False,
                                    callback=self.getDetectionResults, rotation_flag=self.rotation_flag
                                )
        self.cardDetectionWorker.start()
        # CardDetection.detect_video(self.capture, display=False, debug=False, filtering=False, callback=self.getDetectionResults, rotation_flag=self.rotation_flag)
        # CardDetection.detect_video(self.capture, display=True, debug=True, filtering=False, callback=self.getDetectionResults, rotation_flag=self.rotation_flag)

        self.isRunning = True

    def stopCamera(self):
        if self.isRunning:
            if hasattr(self, 'worker'):
                self.cardDetectionWorker.quit()
            if hasattr(self, 'capture'):
                self.capture.release()
            self.rotate_frame.setHidden(True)
            self.video_label.clear()
            self.isRunning = False
            print() # print a new line


    def getDetectionResults(self, det_cards, img_result):
        # if self.rotation_flag:
        #     img_result = cv2.rotate(img_result, self.rotation_flag)
            
        #     h,w,ch = img_result.shape
        #     self.rotate_frame.setGeometry(w-5, -5, 50, 50)
        #     if self.rotation_flag == cv2.ROTATE_90_COUNTERCLOCKWISE \
        #             or self.rotation_flag == cv2.ROTATE_90_CLOCKWISE:
        #         d = (h-w)//2
        #         img_result = img_result[d:w+d, :w]

        pixmap = QPixmap(QImage(
            img_result,
            img_result.shape[1],
            img_result.shape[0],
            QImage.Format_BGR888)
        )#.scaledToWidth(self.video_label.width(), Qt.SmoothTransformation)
        self.video_label.setPixmap(pixmap)
        self.video_label.update()

        det_cards = pd.DataFrame(det_cards)
        self.detectionHelper(det_cards)

        # if not res.empty:
        #     print('result:', res[['name','set_id']].values.tolist())
        #     self.addCardsToTableView(res)


####################################################################################
####################################################################################


class DetectionHelper(QObject):
    '''
    helper class for calculating which card should be added to the main dataframe.
    '''
    results = pyqtSignal(pd.DataFrame, pd.DataFrame)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_call_time = None
        self.frame_times = []
        self.fps = 30
        self.cards_buffer = pd.DataFrame(columns=['name','frames_on_screen']) # columns=['frames_on_screen'] + ['name', 'set_id', 'card_id', 'cnt', 'img_warp', 'hash_diff', 'phash']
        self.phash_df = pHash.get_pHash_df(update=False).copy()

    def update_frame_times(self, N=30):
        current_call_time = timeit.default_timer()
        if self.last_call_time is not None:
            self.frame_times += [ current_call_time - self.last_call_time ]

        # only keep last N frame times
        if len(self.frame_times) > N:
            self.frame_times = self.frame_times[1:N+1]

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
            # self.update_card_price_in_phashdf(plus)
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
                self.results.emit(res.copy(), res_info.copy())
        except Exception as e:
            print(e, file=sys.stderr)
