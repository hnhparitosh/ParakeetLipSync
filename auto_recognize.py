from allosaurus.app import read_recognizer
from PySide6.QtCore import QRunnable, QObject, Slot, Signal
import json

class AutoRecognize(QRunnable):
    
    def __init__(self, sound_path):
        # defining custom signal
        class WorkerSignals(QObject):
            result = Signal(object)

        super(AutoRecognize, self).__init__()
        self.file_name = sound_path
        print("AutoRecognize object created\n")
        self.signals = WorkerSignals()
    
    def ipa_to_preston_blair(self, input):
        with open("ipa_preston_blair.json", encoding="utf8") as f:
            ipa_preston_map = json.load(f)
        
        new_words = []
        for line in input.split('\n'):
            if line:
                start_time, duration, ipa = line.split()
                preston_blair = ipa_preston_map.get(ipa, "rest")
                new_words.append(f"{start_time} {duration} {preston_blair}")
                
        return "\n".join(new_words)
    
    @Slot()
    def run(self):
        # Run the audio processing code in a separate thread
        model = read_recognizer()
        ipa_output = model.recognize(self.file_name, timestamp=True)
        # Emit the "result" signal with the output
        output = self.ipa_to_preston_blair(ipa_output)
        print("about to emit the output")
        self.signals.result.emit(output)
    