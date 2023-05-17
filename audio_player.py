import librosa
import sounddevice as sd
# from PySide6.QtCore import QRunnable

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

# running the audio player in the main application rather than a separate thread

# class AudioWorker(QRunnable):
#     def __init__(self, audio_player, audio_file):
#         super().__init__()
#         self.audio_player = audio_player
#         self.audio_file = audio_file

#     def run(self):
#         self.audio_player.load_audio(self.audio_file)
#         self.audio_player.play_audio()

## Example usage
# if __name__ == "__main__":
#     player = AudioPlayer()
#     audio_file = "D:/setups/Lipsync/lame.wav"

#     player.load_audio(audio_file)
#     player.play_audio()
#     sd.wait()
    # Wait for some time while audio is playing
    # player.pause_audio()
