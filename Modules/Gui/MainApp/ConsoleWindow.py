import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

MAX_LINE_COUNT = 100

class ConsoleWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Console Window')
        self.setWindowFlags(Qt.Dialog)

        self.text_box = QTextEdit(parent=self)
        self.text_box.setReadOnly(True)
        self.text_box.setTextInteractionFlags(Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse)
        self.text_box.setStyleSheet('background-color:#e1e1e1')
        self.text_box.setFont(QFont('consolas', 11))
        self.text_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.text_box.document().setMaximumBlockCount(MAX_LINE_COUNT)

        widget = QWidget()
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        vbox.setSpacing(0)
        hbox.setSpacing(0)
        btn = QPushButton('Clear')
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.clicked.connect(self.text_box.clear)
        # spacer = QSpacerItem(0, 1000, QSizePolicy.Expanding, QSizePolicy.Minimum)
        # hbox.addItem(spacer)
        hbox.addStretch()
        hbox.addWidget(btn)
        vbox.addItem(hbox)
        vbox.addWidget(self.text_box)
        widget.setLayout(vbox)
        self.setCentralWidget(widget)
        
        # vscroll = self.text_box.verticalScrollBar()
        # vscroll.setStyle(QStyleFactory.create('WindowsVista'))
        
        self.override_std()

    def override_std(self):
        sys.stdout = OutLog(self.text_box, sys.stdout, color='black')
        sys.stderr = OutLog(self.text_box, sys.stderr, color='red')

        sys.stdout.write_signal.connect(self.write_signal)
        sys.stdout.tqdm_signal.connect(self.tqdm_signal)

        sys.stderr.write_signal.connect(self.write_signal)
        sys.stderr.tqdm_signal.connect(self.tqdm_signal)

    def tqdm_signal(self, m, color):
        # delete last block
        self.text_box.moveCursor(QTextCursor.End)
        cursor = self.text_box.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        # cursor.select(QTextCursor.BlockUnderCursor)
        cursor.removeSelectedText()
        
        # write the next line
        self.write_signal(m, color)

    def write_signal(self, m, color):
        self.text_box.moveCursor(QTextCursor.End)
        if m == '\n':
            self.text_box.textCursor().insertBlock()
        else:
            self.text_box.setTextColor(QColor(color))
            self.text_box.insertPlainText(m)
            # self.text_box.append(m)
        
        # lineCount = self.text_box.document().lineCount()
        # if lineCount > MAX_LINE_COUNT:
        #     self.text_box.moveCursor(QTextCursor.Start)
        #     cursor = self.text_box.textCursor()
        #     cursor.select(QTextCursor.LineUnderCursor)
        #     cursor.removeSelectedText()
        
        self.text_box.verticalScrollBar().setValue(self.text_box.verticalScrollBar().maximum()) # scroll to bottom

class OutLog(QObject):
    write_signal = pyqtSignal(str, str)
    tqdm_signal = pyqtSignal(str, str)

    def __init__(self, edit, out, color='black'):
        QObject.__init__(self)
        self.edit = edit
        self.out = out
        self.color = color

    def flush(self):
        pass

    def write(self, m):
        if m != '':
            if self.out:
                self.out.write(m)

            if '\r' in m:
                m = m.replace('\r', '')
                self.tqdm_signal.emit(m, self.color)
            else:
                # m = m.replace('\n', '<br />')
                # self.edit.insertHtml(f'<span><font color={self.color}>{m}</font></span>')
                # self.edit.insertPlainText(m)
                self.write_signal.emit(m, self.color)