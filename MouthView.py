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