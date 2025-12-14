"""Audio player with position tracking and playback controls."""

import time
import threading
from typing import Callable, Optional

import librosa
import numpy as np
import sounddevice as sd


class AudioPlayer:
    """Audio player with position tracking and seek functionality."""

    def __init__(self):
        self.samples: Optional[np.ndarray] = None
        self.sample_rate: Optional[int] = None
        self.duration: float = 0.0

        # Playback state
        self.is_playing: bool = False
        self.current_position: int = 0  # Position in samples
        self._play_start_sample: int = 0
        self._play_end_sample: Optional[int] = None
        self._play_start_time: float = 0.0

        # Callbacks
        self._on_position_update: Optional[Callable[[float], None]] = None
        self._on_playback_finished: Optional[Callable[[], None]] = None

        # Position update thread
        self._update_thread: Optional[threading.Thread] = None
        self._stop_update_thread: bool = False

    def load(self, file_path: str) -> tuple[np.ndarray, int]:
        """Load audio file and return samples and sample rate."""
        self.stop()
        self.samples, self.sample_rate = librosa.load(file_path, sr=None)
        self.duration = len(self.samples) / self.sample_rate if self.sample_rate else 0
        self.current_position = 0
        self._play_start_sample = 0
        self._play_end_sample = None
        return self.samples, self.sample_rate

    def get_position_seconds(self) -> float:
        """Return current position in seconds."""
        if self.sample_rate and self.samples is not None:
            return min(self.current_position / self.sample_rate, self.duration)
        return 0.0

    def seek(self, position_seconds: float) -> None:
        """Seek to a position in seconds."""
        if self.samples is not None and self.sample_rate is not None:
            was_playing = self.is_playing
            if was_playing:
                self.stop()

            self.current_position = int(position_seconds * self.sample_rate)
            self.current_position = max(0, min(self.current_position, len(self.samples)))

            if was_playing:
                self.play()

    def play(self) -> None:
        """Play audio from current position."""
        if self.samples is None or self.sample_rate is None:
            return

        # Stop any current playback without clearing end_sample
        self._stop_playback()

        start = self.current_position
        end = self._play_end_sample if self._play_end_sample else len(self.samples)

        if start >= end or start >= len(self.samples):
            return

        audio_slice = self.samples[start:end]
        self._play_start_sample = start
        self._play_start_time = time.time()

        sd.play(audio_slice, self.sample_rate)
        self.is_playing = True
        self._start_position_updates()

    def play_from(self, position_seconds: float) -> None:
        """Play from specified position to the end."""
        if self.samples is not None and self.sample_rate is not None:
            self._play_end_sample = None  # Play to end
            self.current_position = int(position_seconds * self.sample_rate)
            self.current_position = max(0, min(self.current_position, len(self.samples)))
            self.play()

    def play_to(self, position_seconds: float) -> None:
        """Play from beginning to specified position."""
        if self.samples is not None and self.sample_rate is not None:
            self.current_position = 0
            self._play_end_sample = int(position_seconds * self.sample_rate)
            self._play_end_sample = max(0, min(self._play_end_sample, len(self.samples)))
            self.play()

    def pause(self) -> None:
        """Pause audio playback, maintaining position."""
        if self.is_playing:
            self._update_current_position()
            self._stop_playback()

    def stop(self) -> None:
        """Stop audio playback and reset end position."""
        self._stop_playback()
        self._play_end_sample = None

    def _stop_playback(self) -> None:
        """Stop audio playback without clearing end position."""
        sd.stop()
        self.is_playing = False
        self._stop_position_updates()

    def toggle(self) -> None:
        """Toggle between play and pause."""
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def set_position_callback(self, callback: Callable[[float], None]) -> None:
        """Set callback for position updates."""
        self._on_position_update = callback

    def set_finished_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for playback finished."""
        self._on_playback_finished = callback

    def _update_current_position(self) -> None:
        """Update current position based on elapsed time."""
        if not self.is_playing or self.samples is None or self.sample_rate is None:
            return

        elapsed = time.time() - self._play_start_time
        self.current_position = self._play_start_sample + int(elapsed * self.sample_rate)

        end_sample = self._play_end_sample if self._play_end_sample else len(self.samples)
        if self.current_position >= end_sample:
            self.current_position = end_sample
            self.is_playing = False
            # Don't call _stop_position_updates here - let the loop exit naturally
            # and call the finished callback
            if self._on_playback_finished:
                self._on_playback_finished()

    def _position_update_loop(self) -> None:
        """Background thread for position updates."""
        while not self._stop_update_thread and self.is_playing:
            self._update_current_position()
            if self._on_position_update and self.is_playing:
                self._on_position_update(self.get_position_seconds())
            time.sleep(0.05)  # 50ms update interval

    def _start_position_updates(self) -> None:
        """Start the position update thread."""
        self._stop_update_thread = False
        self._update_thread = threading.Thread(target=self._position_update_loop, daemon=True)
        self._update_thread.start()

    def _stop_position_updates(self) -> None:
        """Stop the position update thread."""
        self._stop_update_thread = True
        # Don't join if called from within the thread itself
        current_thread = threading.current_thread()
        if self._update_thread and self._update_thread.is_alive() and self._update_thread != current_thread:
            self._update_thread.join(timeout=0.2)
