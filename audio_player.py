import librosa
import sounddevice as sd

class AudioPlayer:
    def __init__(self):
        self.y = None
        self.sr = None
        self.stream = None

    def load_audio(self, file_path):
        self.y, self.sr = librosa.load(file_path, sr=None)

    def play_audio(self):
        if self.y is not None and self.sr is not None:
            print('---------- playing audio -----------')
            self.stream = sd.play(self.y, self.sr)
            # sd.wait()

    def pause_audio(self):
        if self.stream is not None:
            sd.stop(self.stream)