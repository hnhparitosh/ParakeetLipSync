from allosaurus.app import read_recognizer
from PySide6.QtCore import Qt, QThreadPool, QRunnable, QObject, Slot, Signal

class AutoRecognize(QRunnable):
    
    def __init__(self, sound_path):
        # defining custom signal
        class WorkerSignals(QObject):
            result = Signal(object)

        super(AutoRecognize, self).__init__()
        self.file_name = sound_path
        print("AutoRecognize object created\n")
        self.signals = WorkerSignals()
    
    @Slot()
    def run(self):
        # Run the audio processing code in a separate thread
        model = read_recognizer()
        output = model.recognize(self.file_name, timestamp=True)
        # Emit the "result" signal with the output
        print("about to emit the output")
        self.signals.result.emit(output)
    
    def convert_to_CMU(input):
        pass