import os, bcrypt
from pymongo import MongoClient
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from . import CustomWidget

class LoginWidget(CustomWidget):
    def __init__(self, parent, root_window):
        CustomWidget.__init__(self, parent, root_window)

        layout = QVBoxLayout()
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        self.setLayout(layout)

        self.username_input = QLineEdit()
        self.username_feedback = QLabel(' ')
        self.username_feedback.setStyleSheet('color: red')
        hbox = QHBoxLayout()
        hbox.addWidget(self.username_input)
        hbox.addWidget(self.username_feedback)
        form_layout.addRow('Username:', hbox)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_feedback = QLabel(' ')
        self.password_feedback.setStyleSheet('color: red')
        hbox = QHBoxLayout()
        hbox.addWidget(self.password_input)
        hbox.addWidget(self.password_feedback)
        form_layout.addRow('Password:', hbox)

        self.btn_login = QPushButton('login')
        self.btn_login.clicked.connect(self.onClickLogin)
        layout.addWidget(self.btn_login)
    
    def checkLoginInfo(self):
        flag = True
        
        if self.username_input.text() == '':
            flag = False
            self.username_feedback.setText('*')

        if self.password_input.text() == '':
            flag = False
            self.password_feedback.setText('*')

        return flag

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.btn_login.click()
        event.accept()

    def onClickLogin(self):
        if not self.username_input.isEnabled() or not self.password_input.isEnabled():
            # do nothing, the login button was already pressed
            return
        
        self.username_feedback.setText(' ')
        self.password_feedback.setText(' ')       

        if self.checkLoginInfo():
            self.username_input.setDisabled(True)
            self.password_input.setDisabled(True)
            self.root_window.statusBar().showMessage('Logging in..', -1)
            
            self.thread = QThread()
            self.worker = self._Worker(self.username_input.text(), self.password_input.text())
            self.worker.moveToThread(self.thread)
            
            self.thread.started.connect(self.worker.run)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.check_user_info)
            self.worker.finished.connect(self.worker.deleteLater)
            
            self.thread.start()
    
    def check_user_info(self, flag):
        if flag:
            self.root_window.statusBar().showMessage('Success', 2000)
            self.password_input.clear()
            self.root_window.showPage('main', self)
            # self.root_window.showPage('phash')
            # self.root_window.showPage('cardDetector')
        else:
            self.root_window.statusBar().showMessage('Failed', 2000)
            self.username_input.setDisabled(False)
            self.password_input.setDisabled(False)
            self.password_input.clear()

    def onHiddenChange(self, invoker, *args, **kwargs):
        if not self.isHidden():
            self.root_window.setWindowTitle('Login')
            self.root_window.resize(280, 115)
            # self.root_window.setFixedSize(325, 150)
            # self.root_window.setFixedSize(self.root_window.minimumSizeHint())


    class _Worker(QObject):
        finished = pyqtSignal(bool)
        
        def __init__(self, username, password):
            QObject.__init__(self)
            self.username = username
            self.password = password

        def task(self):
            mongo_uri = os.environ.get('MONGO_URI')
            client = MongoClient(mongo_uri)

            db = client['mtg-draftsim']
            users = db['users']

            user = users.find_one({'username': self.username})
            if user is None:
                return False

            password = self.password.encode('utf8')
            password_hash = user['password'].encode('utf8')
            return bcrypt.checkpw(password, password_hash)

        def run(self):
            flag = self.task()
            self.finished.emit(flag)