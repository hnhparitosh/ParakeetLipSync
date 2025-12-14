"""Data models for Parakeet Lipsync."""

from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class PhonemeStep:
    """Represents a single phoneme/mouth shape with timing information."""

    start_time: float  # Start time in seconds
    duration: float  # Duration in seconds
    mouth_shape: str  # Preston-Blair mouth shape (e.g., "MBP", "AI", "rest")

    @property
    def end_time(self) -> float:
        """Return the end time of this phoneme step."""
        return self.start_time + self.duration

    def contains_time(self, time: float) -> bool:
        """Check if the given time falls within this phoneme step."""
        return self.start_time <= time < self.end_time

    def to_string(self) -> str:
        """Convert to string format: 'start_time duration mouth_shape'."""
        return f"{self.start_time:.4f} {self.duration:.4f} {self.mouth_shape}"

    @classmethod
    def from_string(cls, line: str) -> "PhonemeStep | None":
        """Parse a phoneme step from a string line.

        Expected format: 'start_time duration mouth_shape'
        Returns None if parsing fails.
        """
        parts = line.strip().split()
        if len(parts) >= 3:
            try:
                start_time = float(parts[0])
                duration = float(parts[1])
                mouth_shape = parts[2]
                return cls(start_time=start_time, duration=duration, mouth_shape=mouth_shape)
            except ValueError:
                return None
        return None


@dataclass
class RecognitionResult:
    """Contains the complete lip-sync recognition result."""

    steps: list[PhonemeStep] = field(default_factory=list)

    def __len__(self) -> int:
        """Return the number of phoneme steps."""
        return len(self.steps)

    def __iter__(self) -> Iterator[PhonemeStep]:
        """Iterate over phoneme steps."""
        return iter(self.steps)

    def __getitem__(self, index: int) -> PhonemeStep:
        """Get a phoneme step by index."""
        return self.steps[index]

    @property
    def duration(self) -> float:
        """Return the total duration of all phoneme steps."""
        if not self.steps:
            return 0.0
        return max(step.end_time for step in self.steps)

    @property
    def is_empty(self) -> bool:
        """Check if the result contains any phoneme steps."""
        return len(self.steps) == 0

    def add_step(self, step: PhonemeStep) -> None:
        """Add a phoneme step to the result."""
        self.steps.append(step)

    def get_shape_at(self, time: float) -> PhonemeStep | None:
        """Get the phoneme step at a given time.

        Returns None if no step contains the given time.
        """
        for step in self.steps:
            if step.contains_time(time):
                return step
        return None

    def to_string(self) -> str:
        """Convert to multi-line string format.

        Each line: 'start_time duration mouth_shape'
        """
        return "\n".join(step.to_string() for step in self.steps)

    @classmethod
    def from_string(cls, data: str) -> "RecognitionResult":
        """Parse recognition result from multi-line string.

        Expected format: one 'start_time duration mouth_shape' per line.
        """
        result = cls()
        for line in data.strip().split("\n"):
            if line.strip():
                step = PhonemeStep.from_string(line)
                if step:
                    result.add_step(step)
        return result

    def export_as_moho_timesheet(self, fps: int = 24) -> str:
        """Export as Moho/Anime Studio timesheet format.

        Args:
            fps: Frames per second for the animation.

        Returns:
            Moho timesheet formatted string starting with 'MohoSwitch1'.
        """
        frames: list[str] = []

        for step in self.steps:
            start_frame = int(step.start_time * fps) + 1
            end_frame = start_frame + int(step.duration * fps)
            frames.extend(f"{i} {step.mouth_shape}" for i in range(start_frame, end_frame))

        return "MohoSwitch1\n" + "\n".join(frames)

    def export_as_text(self) -> str:
        """Export as plain text format (alias for to_string)."""
        return self.to_string()
