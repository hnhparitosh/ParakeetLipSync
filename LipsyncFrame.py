from PySide6.QtWidgets import QMainWindow, QLabel, QFileDialog, QTextEdit, QWidget, QVBoxLayout, QPushButton
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QThreadPool, Slot
# from PySide6.QtCore import Qt

# from WaveformView import WaveformView
# from MouthView import MouthView
# from DialogueView import DialogueView
from auto_recognize import AutoRecognize
import sys

class LipsyncFame(QMainWindow):
    def __init__(self) :
        super().__init__()
        self.setWindowTitle("Parakeet Lipsync")
        self.resize(500, 500)
        # self.setGeometry(100, 100, 300, 200)


        # defining widgets
        self.label = QLabel(self)
        self.label.setText("Please load an audio file. (Ctrl+O)")

        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("background-color: white; border: none;")
        
        self.process_button = QPushButton("Process", self)
        self.process_button.clicked.connect(self.process_audio)
        self.process_button.setEnabled(False)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.process_button)
        layout.addWidget(self.text_area)
        
        central_widget.setLayout(layout)



        self.menuBar = self.menuBar()

        
        # defining actions
        open_action = QAction('Open file', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.load_audio)

        # adding menus
        fileMenu = self.menuBar.addMenu('File')
        fileMenu.addAction(open_action)

        # creating a thread pool
        self.thread_pool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.thread_pool.maxThreadCount())

    def load_audio(self):
        # method to load a file
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav)")
        file_dialog.setDefaultSuffix("mp3")
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec_() == QFileDialog.Accepted:
            self.file_name = file_dialog.selectedFiles()[0]
            self.label.setText(f"Loaded: {self.file_name}")
            self.process_button.setEnabled(True) 
    
    def process_audio(self):
        # Disable the button while processing the audio
        self.process_button.setEnabled(False)

        worker = AutoRecognize(self.file_name)

        print("worker created")

        # Connect the "finished" signal to the slot that updates the text area
        worker.signals.result.connect(lambda result: self.text_area.append(result))

        print("signal connected")
        # Start the AudioProcessor instance in the thread pool
        # QThreadPool.globalInstance().start(processor)
        self.thread_pool.start(worker)
        print("thread started")
        # Audio processing code here
        # For example, just print some text in the text area
        # self.text_area.append("Audio processing completed.")
    