from PySide6.QtWidgets import (QMainWindow, QLabel, QFileDialog, QTextEdit, QWidget,
                               QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox)
from PySide6.QtGui import QAction
from PySide6.QtCore import QThreadPool
from audio_player import AudioPlayer
from waveform_widget import WaveformWidget

from MouthView import MouthView
from auto_recognize import AutoRecognize
import sys


class LipsyncFrame(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parakeet Lipsync")
        self.resize(700, 600)
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
        self.spin_box.valueChanged.connect(lambda val: setattr(self, 'frame_rate', val))

        # Audio player
        self.audio_player = AudioPlayer()
        self.audio_player.position_updated.connect(self._on_position_updated)
        self.audio_player.playback_finished.connect(self._on_playback_finished)

        # Waveform widget
        self.waveform_widget = WaveformWidget()
        self.waveform_widget.position_changed.connect(self._on_waveform_seek)

        # Playback controls
        self.play_pause_button = QPushButton("Play", self)
        self.play_pause_button.setEnabled(False)
        self.play_pause_button.clicked.connect(self.toggle_playback)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_audio)

        self.play_to_button = QPushButton("Play to Cursor", self)
        self.play_to_button.setEnabled(False)
        self.play_to_button.clicked.connect(self.play_to_cursor)
        self.play_to_button.setToolTip("Play from the beginning to the cursor position")

        self.play_from_button = QPushButton("Play from Cursor", self)
        self.play_from_button.setEnabled(False)
        self.play_from_button.clicked.connect(self.play_from_cursor)
        self.play_from_button.setToolTip("Play from the cursor position to the end")

        # self.mouth_view = MouthView()

        # Layout
        fps_sublayout = QHBoxLayout()
        fps_sublayout.addWidget(self.fps_label)
        fps_sublayout.addWidget(self.spin_box)
        fps_sublayout.addStretch()

        playback_controls_layout = QHBoxLayout()
        playback_controls_layout.addWidget(self.play_pause_button)
        playback_controls_layout.addWidget(self.stop_button)
        playback_controls_layout.addWidget(self.play_to_button)
        playback_controls_layout.addWidget(self.play_from_button)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.addLayout(fps_sublayout)
        layout.addWidget(self.fileName_label)
        layout.addWidget(self.waveform_widget)
        layout.addLayout(playback_controls_layout)
        layout.addWidget(self.process_button)
        layout.addWidget(self.text_area)
        # layout.addWidget(self.mouth_view)

        central_widget.setLayout(layout)

        self.menuBar = self.menuBar()

        # defining actions
        open_action = QAction('Open file', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.load_audio)

        save_action = QAction('Save file', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_output)

        export_moho = QAction('Export Moho Timesheet', self)
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

            # Update waveform display
            samples, sample_rate = self.audio_player.get_audio_data()
            self.waveform_widget.set_audio_data(samples, sample_rate)

            # Enable controls
            self.process_button.setEnabled(True)
            self._enable_playback_controls(True)

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

    def save_output(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt)")

        if file_name:
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

    def toggle_playback(self):
        """Toggle between play and pause."""
        if self.audio_player.is_playing:
            self.audio_player.pause_audio()
            self.play_pause_button.setText("Play")
        else:
            self.audio_player.play_audio_fresh()
            self.play_pause_button.setText("Pause")

    def stop_audio(self):
        """Stop playback and reset to beginning."""
        self.audio_player.stop()
        self.audio_player.current_position = 0
        self.waveform_widget.set_position(0)
        self.play_pause_button.setText("Play")

    def play_to_cursor(self):
        """Play from beginning to the current cursor position."""
        cursor_position = self.waveform_widget.get_position_seconds()
        if cursor_position > 0:
            self.audio_player.play_to_position(cursor_position)
            self.play_pause_button.setText("Pause")

    def play_from_cursor(self):
        """Play from the current cursor position to the end."""
        cursor_position = self.waveform_widget.get_position_seconds()
        self.audio_player.play_from_position(cursor_position)
        self.play_pause_button.setText("Pause")

    def _on_position_updated(self, position_seconds):
        """Handle position updates from audio player."""
        self.waveform_widget.set_position(position_seconds)

    def _on_waveform_seek(self, position_seconds):
        """Handle seek from waveform widget click."""
        self.audio_player.seek(position_seconds)

    def _on_playback_finished(self):
        """Handle playback completion."""
        self.play_pause_button.setText("Play")

    def _enable_playback_controls(self, enabled):
        """Enable or disable all playback controls."""
        self.play_pause_button.setEnabled(enabled)
        self.stop_button.setEnabled(enabled)
        self.play_to_button.setEnabled(enabled)
        self.play_from_button.setEnabled(enabled)
