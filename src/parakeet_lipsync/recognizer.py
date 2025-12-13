"""Phoneme recognition using Allosaurus model."""

import json
import threading
from pathlib import Path
from typing import Callable, Optional

from allosaurus.app import read_recognizer


# IPA to Preston-Blair mouth shape mapping
IPA_PRESTON_BLAIR_MAP = {
    "b": "MBP", "ʧ": "WQ", "d": "E", "ð": "L", "f": "FV", "g": "E",
    "h": "E", "ʤ": "WQ", "k": "E", "l": "L", "m": "MBP", "n": "etc",
    "ŋ": "E", "p": "MBP", "r": "L", "s": "etc", "ʃ": "WQ", "t": "E",
    "θ": "E", "v": "FV", "w": "WQ", "j": "E", "z": "etc", "ʒ": "WQ",
    "ɑ": "AI", "æ": "AI", "ə": "E", "ʌ": "E", "ɔ": "O", "ɛ": "E",
    "ɚ": "WQ", "ɝ": "WQ", "ɪ": "AI", "i": "E", "ʊ": "U", "u": "U",
    "aʊ": "WQ", "aɪ": "AI", "eɪ": "E", "oʊ": "WQ", "o": "O", "ɔɪ": "WQ",
    "e": "E", "a": "AI", "ʔ": "rest", "ɒ": "O", "ɯ": "U", "ɹ": "L",
    "ɻ": "L", "-": "rest", "ɡ": "E", "x": "N"
}


class PhonemeRecognizer:
    """Handles phoneme recognition and conversion to mouth shapes."""

    def __init__(self):
        self._model = None
        self._is_processing = False
        self._worker_thread: Optional[threading.Thread] = None

    def _load_model(self):
        """Lazy load the Allosaurus model."""
        if self._model is None:
            print("Loading Allosaurus model...")
            self._model = read_recognizer()
            print("Model loaded.")

    @staticmethod
    def ipa_to_preston_blair(ipa_output: str) -> str:
        """Convert IPA phonemes to Preston-Blair mouth shapes.

        Args:
            ipa_output: IPA output from allosaurus (format: "start duration phoneme" per line)

        Returns:
            Converted output with Preston-Blair mouth shapes
        """
        result_lines = []
        for line in ipa_output.strip().split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 3:
                    start_time, duration, ipa = parts[0], parts[1], parts[2]
                    mouth_shape = IPA_PRESTON_BLAIR_MAP.get(ipa, "rest")
                    result_lines.append(f"{start_time} {duration} {mouth_shape}")
        return "\n".join(result_lines)

    def recognize(self, audio_path: str) -> str:
        """Synchronously recognize phonemes from audio file.

        Args:
            audio_path: Path to the audio file

        Returns:
            Preston-Blair mouth shapes with timestamps
        """
        self._load_model()
        ipa_output = self._model.recognize(audio_path, timestamp=True)
        return self.ipa_to_preston_blair(ipa_output)

    def recognize_async(
        self,
        audio_path: str,
        on_complete: Callable[[str], None],
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        """Asynchronously recognize phonemes from audio file.

        Args:
            audio_path: Path to the audio file
            on_complete: Callback with result string
            on_error: Optional callback for errors
        """
        if self._is_processing:
            return

        def worker():
            self._is_processing = True
            try:
                result = self.recognize(audio_path)
                on_complete(result)
            except Exception as e:
                if on_error:
                    on_error(e)
                else:
                    print(f"Recognition error: {e}")
            finally:
                self._is_processing = False

        self._worker_thread = threading.Thread(target=worker, daemon=True)
        self._worker_thread.start()

    @property
    def is_processing(self) -> bool:
        """Return True if recognition is in progress."""
        return self._is_processing


def export_moho_timesheet(lipsync_data: str, fps: int = 24) -> str:
    """Convert lipsync data to Moho timesheet format.

    Args:
        lipsync_data: Lipsync data (format: "start duration mouth" per line)
        fps: Frames per second

    Returns:
        Moho timesheet formatted string
    """
    frames = []
    for line in lipsync_data.strip().split('\n'):
        if line:
            parts = line.split()
            if len(parts) >= 3:
                start_time, duration, mouth = parts[0], parts[1], parts[2]
                start_frame = int(float(start_time) * fps) + 1
                end_frame = start_frame + int(float(duration) * fps)
                frames.extend([f'{i} {mouth}' for i in range(start_frame, end_frame)])

    return 'MohoSwitch1\n' + '\n'.join(frames)
