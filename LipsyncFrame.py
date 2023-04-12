from PySide6.QtWidgets import QMainWindow, QApplication, QGridLayout, QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

# from WaveformView import WaveformView
# from MouthView import MouthView
# from DialogueView import DialogueView
import sys

class LipsyncFame(QMainWindow):
    def __init__(self) :
        super().__init__()
        self.setWindowTitle("Parakeet Lipsync")
        self.resize(500, 500)

        self.menuBar = self.menuBar()

        # adding menus
        fileMenu = self.menuBar.addMenu('File')

        # defining actions
        open_action = QAction('Open file', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(  )

        # defining widgets


        # layout = QVBoxLayout()
        # layout.addWidget(WaveformView,0,0)
        # layout.addWidget(DialogueView,1,0)
        # layout.addWidget(MouthView,1,1)

        # widget = QWidget()
        # widget.setLayout(layout)

        # self.setCentralWidget(widget)