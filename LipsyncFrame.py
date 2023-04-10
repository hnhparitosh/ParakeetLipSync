from PySide6.QtWidgets import QMainWindow, QPushButton, QApplication, QGridLayout, QWidget
from WaveformView import WaveformView
from MouthView import MouthView
from DialogueView import DialogueView
import sys

class LipsyncFame(QMainWindow):
    def __init__(self) :
        super().__init__()
        self.setWindowTitle("Parakeet Lipsync")
        
        layout = QGridLayout()
        layout.addWidget(WaveformView,0,0)
        layout.addWidget(DialogueView,1,0)
        layout.addWidget(MouthView,1,1)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)