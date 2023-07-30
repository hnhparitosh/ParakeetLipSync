from PySide6.QtWidgets import QMainWindow, QLabel, QFileDialog, QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox
from PySide6.QtGui import QAction
from PySide6.QtCore import QThreadPool
from audio_player import AudioPlayer

from MouthView import MouthView
from auto_recognize import AutoRecognize
import sys

class LipsyncFrame(QMainWindow):
    def __init__(self) :
        super().__init__()
        self.setWindowTitle("Parakeet Lipsync")
        self.resize(500, 500)
        # self.setGeometry(100, 100, 300, 200)
        self.frame_rate = 24

        # defining widgets
        self.fileName_label = QLabel(self)
        self.fileName_label.setText("Please load an audio file. (Ctrl+O)")

        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("background-color: white; border: none;")
        
        self.process_button = QPushButton("Process", self)
        self.process_button.clicked.connect(self.process_audio)
        self.process_button.setEnabled(False)

        # Add a spin box widget to set the frame rate
        self.fps_label = QLabel("FPS:", self)
        self.spin_box = QSpinBox(self)
        self.spin_box.setRange(24, 60)
        self.spin_box.setValue(self.frame_rate)
        self.spin_box.valueChanged.connect(lambda val: setattr(self,'frame_rate', val))

        # sound controls and mouthView
        self.audio_player = AudioPlayer()

        self.play_button = QPushButton("Play", self)
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.play_audio)

        self.pause_button = QPushButton("Pause", self)
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause_audio)
        
        # self.mouth_view = MouthView()

        fps_sublayout = QHBoxLayout()
        fps_sublayout.addWidget(self.fps_label)
        fps_sublayout.addWidget(self.spin_box)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.addLayout(fps_sublayout)
        layout.addWidget(self.fileName_label)
        layout.addWidget(self.process_button)
        layout.addWidget(self.text_area)
        # layout.addWidget(self.mouth_view)
        layout.addWidget(self.play_button)
        layout.addWidget(self.pause_button)
        
        central_widget.setLayout(layout)

        self.menuBar = self.menuBar()

        # defining actions
        open_action = QAction('Open file', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.load_audio)

        save_action = QAction('Save file', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_output)

        export_moho = QAction('Export Moho Timesheet',self)
        export_moho.triggered.connect(self.export_moho)

        # adding menus
        fileMenu = self.menuBar.addMenu('File')
        fileMenu.addAction(open_action)
        fileMenu.addAction(save_action)
        fileMenu.addAction(export_moho)

        # creating a thread pool
        self.thread_pool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.thread_pool.maxThreadCount())

    def load_audio(self):
        # method to load a file
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav)")
        file_dialog.setDefaultSuffix("wav")
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec_() == QFileDialog.Accepted:
            self.file_name = file_dialog.selectedFiles()[0]

            # loading the file in audio player
            self.audio_player.load_audio(self.file_name)
            self.fileName_label.setText(f"Loaded: {self.file_name}")

            self.process_button.setEnabled(True)
            self.play_button.setEnabled(True)
            self.pause_button.setEnabled(True) 
    
    def process_audio(self):
        # Disable the button while processing the audio
        self.process_button.setEnabled(False)

        worker = AutoRecognize(self.file_name)
        print("auto recognition worker created")

        # Connect the "finished" signal to the slot that updates the text area
        worker.signals.result.connect(lambda result: self.text_area.setText(result))

        # Start the AudioProcessor instance in the thread pool
        self.thread_pool.start(worker)
        print("thread started")
        # self.text_area.append("Audio processing completed.")
    
    def save_output(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt)")

        if file_name:
        # Open the selected file in write mode and write the contents of the text editor to the file
            with open(file_name, "w", encoding='utf-8') as f:
                f.write(self.text_area.toPlainText())

    def export_moho(self):
        frames = []
        data = self.text_area.toPlainText()
        framerate = self.frame_rate
        for line in data.split('\n'):
            if line:
                start_time, duration, mouth = line.split()
                start_frame = int(float(start_time) * framerate) + 1
                end_frame = start_frame + int(float(duration) * framerate)
                frames.extend([f'{i} {mouth}' for i in range(start_frame, end_frame)])
        
        output = 'MohoSwitch1\n' + '\n'.join(frames)

        file_name, _ = QFileDialog.getSaveFileName(self, "Save Moho Timesheet", "", "Data Files (*.dat)")
        if file_name:
            with open(file_name, "w", encoding='utf-8') as f:
                f.write(output)
    
    def play_audio(self):
        self.audio_player.play_audio()
    
    def pause_audio(self):
        self.audio_player.pause_audio()