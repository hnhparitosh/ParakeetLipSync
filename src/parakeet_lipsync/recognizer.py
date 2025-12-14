"""Phoneme recognition using Allosaurus model."""

import threading
from typing import Callable, Optional

from allosaurus.app import read_recognizer

from parakeet_lipsync.models import PhonemeStep, RecognitionResult


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
    def _parse_ipa_output(ipa_output: str) -> RecognitionResult:
        """Parse IPA output from Allosaurus and convert to RecognitionResult.

        Args:
            ipa_output: IPA output from allosaurus (format: "start duration phoneme" per line)

        Returns:
            RecognitionResult with Preston-Blair mouth shapes
        """
        result = RecognitionResult()

        for line in ipa_output.strip().split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        start_time = float(parts[0])
                        duration = float(parts[1])
                        ipa = parts[2]
                        mouth_shape = IPA_PRESTON_BLAIR_MAP.get(ipa, "rest")

                        step = PhonemeStep(
                            start_time=start_time,
                            duration=duration,
                            mouth_shape=mouth_shape
                        )
                        result.add_step(step)
                    except ValueError:
                        continue

        return result

    def recognize(self, audio_path: str) -> RecognitionResult:
        """Synchronously recognize phonemes from audio file.

        Args:
            audio_path: Path to the audio file

        Returns:
            RecognitionResult containing mouth shapes with timestamps
        """
        self._load_model()
        ipa_output = self._model.recognize(audio_path, timestamp=True)
        return self._parse_ipa_output(ipa_output)

    def recognize_async(
        self,
        audio_path: str,
        on_complete: Callable[[RecognitionResult], None],
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        """Asynchronously recognize phonemes from audio file.

        Args:
            audio_path: Path to the audio file
            on_complete: Callback with RecognitionResult
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
