import os
import librosa
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap, QImage, QPainter


class MouthView(QGraphicsView):
    def __init__(self, fileName, parent=None):
        super().__init__(parent)

        self.mouth_images = {}
        
        self.fileName = fileName

        self.audioFile = None
        self.audio_stream = None
        self.current_time = 0
        self.current_phoneme = None
        self.startTime = 0
        self.endTime = 0

        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        # self.setFixedSize(100, 100)
        
        self.mouth_images = {}
        self.load_mouth_images()
    
    def set_audio_file(self, filename):
        self.audio_file = filename
        self.audio_stream = librosa.load(filename)

    def play(self):
        if self.audio_file is None:
            return

        self.audio_stream.play()
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        self.mouth_image = self.mouth_images[self.current_phoneme]

        painter = QPainter(self)
        painter.drawImage(event.rect(), self.mouth_image)
    
    def load_mouth_images(self):
        mouth_images_dir = os.path.join(os.path.dirname(__file__), 'mouthImages')
        for filename in os.listdir(mouth_images_dir):
            if filename.endswith('.jpg'):
                mouth_name = os.path.splitext(filename)[0]
                mouth_path = os.path.join(mouth_images_dir, filename)
                self.mouth_images[mouth_name] = QPixmap(mouth_path)
    
    def update_mouth(self, time, duration, mouth_shape):
        if mouth_shape in self.mouth_images:
            self.scene.clear()
            mouth_pixmap = self.mouth_images[mouth_shape]
            mouth_item = QGraphicsPixmapItem(mouth_pixmap)
            self.scene.addItem(mouth_item)
            
            # Position the mouth item based on the time and duration
            mouth_width = mouth_pixmap.width()
            mouth_height = mouth_pixmap.height()
            mouth_item.setPos(self.width() * time / self.parent().audio_duration - mouth_width / 2, self.height() / 2 - mouth_height / 2)

# class MouthView(QWidget):
#     def __init__(self):
#         super().__init__()

#         self.play_button = QPushButton("Play Audio")
#         self.play_button.clicked.connect(self.play_audio)

#         self.stop_button = QPushButton("Stop Audio")
#         self.stop_button.setDisabled(True)
#         self.stop_button.clicked.connect(self.stop_audio)

#         self.mouth_label = QLabel()
#         self.mouth_label.setAlignment(Qt.AlignCenter)
#         self.movie = QMovie()
#         self.mouth_label.setMovie(self.movie)

#         layout = QVBoxLayout()
#         layout.addWidget(self.play_button)
#         layout.addWidget(self.stop_button)
#         layout.addWidget(self.mouth_label)
#         self.setLayout(layout)

#         self.media_player = QMediaPlayer(self)
#         # self.media_player.stateChanged.connect(self.handle_state_changed)
#         # self.media_player.mediaStatusChanged.connect(self.handle_media_status_changed)

#     def update_image(self, filename):
#         mouth_shape = filename.split("/")[-1].split(".")[0]
#         image_path = os.path.join("mouthImages", f"{mouth_shape}.jpg")
#         self.movie.stop()
#         self.movie.setFileName(image_path)
#         self.movie.start()

#     def handle_state_changed(self, state):
#         if state == QMediaPlayer.StoppedState:
#             self.stop_button.setDisabled(True)
#             self.play_button.setDisabled(False)

#     def handle_media_status_changed(self, status):
#         if status == QMediaPlayer.EndOfMedia:
#             self.media_player.stop()
#             self.stop_button.setDisabled(True)
#             self.play_button.setDisabled(False)

#     def play_audio(self):
#         filename = self.parent().fileName_label.text()
#         url = QUrl.fromLocalFile(filename)
#         # content = QMediaContent(url)
#         self.media_player.setMedia(url)
#         self.media_player.play()
#         self.play_button.setDisabled(True)
#         self.stop_button.setDisabled(False)

#     def stop_audio(self):
#         self.media_player.stop()
#         self.stop_button.setDisabled(True)
#         self.play_button.setDisabled(False)



# class MouthView(QWidget):
#     def __init__(self):
#         super().__init__()

#         self.mouth_label = QLabel()

#         layout = QVBoxLayout()
#         layout.addWidget(self.mouth_label)
#         self.setLayout(layout)

#         self.mouthImages = {}
#         for shape in ['AI', 'E', 'etc', 'FV', 'L', 'MBP', 'O', 'rest', 'U', 'WQ']:
#             self.mouthImages[shape] = QPixmap(f'mouthImages/{shape}.png')
#         self.timer = QTimer()
#         self.timer.timeout.connect(self.update_mouth)

#     def play(self, text_area, file_label):
#         self.text_area = text_area
#         self.file_label = file_label
#         self.processing_result = []
#         for line in self.text_area.toPlainText().split('\n'):
#             if line.strip():
#                 time, duration, shape = line.split()
#                 self.processing_result.append((float(time), float(duration), shape))
#         self.processing_index = 0
#         self.player = QMediaPlayer()
#         self.player.setMedia(QUrl.fromLocalFile(self.file_label.text()))
#         self.player.play()
#         self.timer.start(10)

#     def update_mouth(self):
#         if self.processing_index >= len(self.processing_result):
#             self.timer.stop()
#             return
#         current_time = self.player.position() / 1000.0
#         start_time, duration, shape = self.processing_result[self.processing_index]
#         end_time = start_time + duration
#         if current_time >= start_time and current_time < end_time:
#             self.mouth_label.setPixmap(self.mouthImages[shape])
#         elif current_time >= end_time:
#             self.processing_index += 1