import librosa
import sounddevice as sd
import numpy as np
from PySide6.QtCore import QObject, Signal, QTimer


class AudioPlayer(QObject):
    """Audio player with position tracking and seek functionality."""

    position_updated = Signal(float)  # Emits current position in seconds
    playback_finished = Signal()  # Emits when playback completes

    def __init__(self):
        super().__init__()
        self.y = None
        self.sr = None
        self.stream = None
        self.duration = 0.0

        # Playback state
        self.is_playing = False
        self.current_position = 0  # Position in samples
        self.play_start_sample = 0  # Where playback started
        self.play_end_sample = None  # Where playback should stop (None = end of audio)

        # Timer for position updates
        self.position_timer = QTimer()
        self.position_timer.setInterval(50)  # Update every 50ms
        self.position_timer.timeout.connect(self._update_position)

    def load_audio(self, file_path):
        """Load audio file and prepare for playback."""
        self.stop()
        self.y, self.sr = librosa.load(file_path, sr=None)
        self.duration = len(self.y) / self.sr if self.sr else 0
        self.current_position = 0
        self.play_start_sample = 0
        self.play_end_sample = None

    def get_audio_data(self):
        """Return audio samples and sample rate."""
        return self.y, self.sr

    def get_duration(self):
        """Return audio duration in seconds."""
        return self.duration

    def get_position_seconds(self):
        """Return current position in seconds."""
        if self.sr:
            return self.current_position / self.sr
        return 0.0

    def seek(self, position_seconds):
        """Seek to a position in seconds."""
        if self.y is not None and self.sr is not None:
            was_playing = self.is_playing
            if was_playing:
                self.stop()

            self.current_position = int(position_seconds * self.sr)
            self.current_position = max(0, min(self.current_position, len(self.y)))

            if was_playing:
                self.play_audio()

    def play_audio(self):
        """Play audio from current position."""
        if self.y is not None and self.sr is not None:
            self.stop()

            # Determine the slice to play
            start = self.current_position
            end = self.play_end_sample if self.play_end_sample else len(self.y)

            if start >= end or start >= len(self.y):
                return

            audio_slice = self.y[start:end]
            self.play_start_sample = start

            print(f'---------- playing audio from {self.get_position_seconds():.2f}s -----------')
            sd.play(audio_slice, self.sr)
            self.is_playing = True
            self.position_timer.start()

    def play_from_position(self, position_seconds):
        """Play audio starting from specified position to the end."""
        if self.y is not None and self.sr is not None:
            self.current_position = int(position_seconds * self.sr)
            self.current_position = max(0, min(self.current_position, len(self.y)))
            self.play_end_sample = None  # Play to end
            self.play_audio()

    def play_to_position(self, position_seconds):
        """Play audio from beginning to specified position."""
        if self.y is not None and self.sr is not None:
            self.current_position = 0
            self.play_end_sample = int(position_seconds * self.sr)
            self.play_end_sample = max(0, min(self.play_end_sample, len(self.y)))
            self.play_audio()

    def pause_audio(self):
        """Pause audio playback, maintaining position."""
        if self.is_playing:
            # Calculate current position before stopping
            self._update_position()
            sd.stop()
            self.is_playing = False
            self.position_timer.stop()
            print(f'---------- paused at {self.get_position_seconds():.2f}s -----------')

    def stop(self):
        """Stop audio playback and reset end position."""
        sd.stop()
        self.is_playing = False
        self.position_timer.stop()
        self.play_end_sample = None

    def toggle_playback(self):
        """Toggle between play and pause."""
        if self.is_playing:
            self.pause_audio()
        else:
            self.play_audio()

    def _update_position(self):
        """Update current playback position based on elapsed time."""
        if not self.is_playing or self.y is None:
            return

        # Get stream info to determine position
        stream_info = sd.get_stream()
        if stream_info and stream_info.active:
            # Estimate position based on frames played
            # sounddevice doesn't give us exact position, so we estimate
            elapsed_frames = sd.get_stream().frame_count if hasattr(sd.get_stream(), 'frame_count') else 0

            # Use a simpler approach: track time since play started
            import time
            if not hasattr(self, '_play_start_time'):
                self._play_start_time = time.time()

            elapsed = time.time() - self._play_start_time
            self.current_position = self.play_start_sample + int(elapsed * self.sr)

            # Check if we've reached the end
            end_sample = self.play_end_sample if self.play_end_sample else len(self.y)
            if self.current_position >= end_sample:
                self.current_position = end_sample
                self.is_playing = False
                self.position_timer.stop()
                self.playback_finished.emit()
                if hasattr(self, '_play_start_time'):
                    del self._play_start_time

            self.position_updated.emit(self.get_position_seconds())
        else:
            # Stream ended
            self.is_playing = False
            self.position_timer.stop()
            if hasattr(self, '_play_start_time'):
                del self._play_start_time
            self.playback_finished.emit()

    def play_audio_fresh(self):
        """Play audio from current position, resetting the start time tracker."""
        if hasattr(self, '_play_start_time'):
            del self._play_start_time
        import time
        self._play_start_time = time.time()
        self.play_audio()
