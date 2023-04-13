from allosaurus.app import read_recognizer
from PySide6.QtCore import Qt, QThreadPool, QRunnable, QObject, Slot, Signal

class AutoRecognize(QObject):
    finished = Signal(str)
    
    def __init__(self, sound_path):
        super().__init__()
        self.file_name = sound_path
        print("AutoRecognize object created\n")
    
    @Slot()
    def run(self):
        # Run the audio processing code in a separate thread
        # result = audio_processing_code.process_audio_file(self.file_name)
        result = "hello"
        # Emit the "finished" signal with the result
        print("about to emit the result")
        self.finished.emit(result)