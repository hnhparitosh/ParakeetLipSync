import os
from PySide6 import QtCore, QtGui, QtWidgets

class MouthView(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super(MouthView, self).__init__(parent)
        self.mouth_images = {}
        self.current_mouth = None
        self.setAlignment(QtCore.Qt.AlignCenter)

    def load_mouth_images(self, directory_path):
        if os.path.isdir(directory_path):
            for filename in os.listdir(directory_path):
                if filename.endswith(".jpg"):
                    mouth_image_path = os.path.join(directory_path, filename)
                    mouth_image = QtGui.QPixmap(mouth_image_path)
                    self.mouth_images[filename[:-4]] = mouth_image

    def set_current_mouth(self, mouth):
        if mouth != self.current_mouth:
            self.current_mouth = mouth
            if mouth in self.mouth_images:
                self.setPixmap(self.mouth_images[mouth])
            else:
                self.clear()

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.audio_processing_result = QtWidgets.QTextEdit()
        self.play_button = QtWidgets.QPushButton("Play")
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.fps_label = QtWidgets.QLabel("FPS:")
        self.fps_spinbox = QtWidgets.QSpinBox()
        self.fps_spinbox.setRange(1, 60)
        self.fps_spinbox.setValue(24)
        self.mouth_view = MouthView()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.audio_processing_result)
        layout.addWidget(self.play_button)
        layout.addWidget(self.stop_button)

        fps_layout = QtWidgets.QHBoxLayout()
        fps_layout.addWidget(self.fps_label)
        fps_layout.addWidget(self.fps_spinbox)
        layout.addLayout(fps_layout)

        layout.addWidget(self.mouth_view)

        self.setLayout(layout)

        self.play_button.clicked.connect(self.play_audio)
        self.stop_button.clicked.connect(self.stop_audio)

    def play_audio(self):
        # TODO: add code to play audio and get phoneme information
        # In the following example, we just set some dummy values
        phoneme_info = [
            ('0.01', '0.045', 'FV'),
            ('0.046', '0.05', 'EY'),
            ('0.051', '0.049', 'OW'),
            ('0.1', '0.04', 'P')
        ]
        for info in phoneme_info:
            time, duration, mouth = info
            self.mouth_view.set_current_mouth(mouth)
            QtCore.QCoreApplication.processEvents()  # update the GUI
            QtWidgets.QApplication.processEvents()  # update the GUI
            QtCore.QThread.msleep(int(1000 / self.fps_spinbox.value()))  # sleep for the specified fps

    def stop_audio(self):
        # TODO: add code to stop audio playback
        pass

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.mouth_view.load_mouth_images("mouthImages")
    window.show()
    app.exec_()
