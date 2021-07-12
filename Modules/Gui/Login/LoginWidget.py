import os #, bcrypt
# from pymongo import MongoClient
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from ..QWorkerThread import QWorkerThread
from ..BaseWidgets.MyQWidget import MyQWidget
from ..MainApp.MainAppWidget import MainAppWidget
from ...Api.auth import AuthApi

class LoginWidget(MyQWidget):
    def __init__(self, parent, root_window:QMainWindow):
        super().__init__(parent, root_window)
        self.root_window.statusBar().showMessage('')

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

        self.checkbox_remember_me = QCheckBox('Remember me')
        self.checkbox_remember_me.setChecked(True)
        layout.addWidget(self.checkbox_remember_me, alignment=Qt.AlignRight)
        
        self.btn_login = QPushButton('login')
        self.btn_login.clicked.connect(self.onClickLogin)
        layout.addWidget(self.btn_login)
    
    def onShow(self):
        self.root_window.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint)
        self.root_window.setWindowTitle('Login')
        self.root_window.resize(280, 115)
        # self.root_window.setFixedSize(325, 150)
        # self.root_window.setFixedSize(self.root_window.minimumSizeHint())

    def validateLoginInfo(self):
        '''
        basic input validation, username and password should not be empty.
        '''
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
        # def _login_task(username, password):
        #     return login(username, password)

        if not self.username_input.isEnabled() \
                or not self.password_input.isEnabled():
            # do nothing, the login button was already pressed
            return
        
        self.username_feedback.setText(' ')
        self.password_feedback.setText(' ')

        if self.validateLoginInfo():
            self.username_input.setDisabled(True)
            self.password_input.setDisabled(True)
            self.checkbox_remember_me.setDisabled(True)
            self.root_window.statusBar().showMessage('Logging in..', -1)
            
            self.worker = QWorkerThread(self, AuthApi.Login, self.username_input.text(), self.password_input.text(), self.checkbox_remember_me.isChecked())
            self.worker.results.connect(self.getWorkerResults)
            self.worker.start()
            # _login_task(self.username_input.text(), self.password_input.text())
            # AuthApi.Login(self.username_input.text(), self.password_input.text(), self.checkbox_remember_me.isChecked())
    
    def getWorkerResults(self, flag:bool):
        if flag:
            self.root_window.statusBar().showMessage('Success', 2000)
            self.password_input.clear()
            self.startMainAppWidget()
            # self.root_window.close()
        else:
            self.root_window.statusBar().showMessage('Failed', 2000)
            self.username_input.setDisabled(False)
            self.password_input.setDisabled(False)
            self.password_input.clear()
            self.checkbox_remember_me.setDisabled(False)
    

    def startMainAppWidget(self):
        mainWidget = MainAppWidget(self.root_window, self.root_window)
        self.root_window.setCentralWidget(mainWidget)
        self.root_window.setWindowFlags(Qt.Window)
        self.root_window.show()
