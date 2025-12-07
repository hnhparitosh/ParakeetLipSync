from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QPen
import numpy as np


class WaveformWidget(QWidget):
    """Widget that displays an audio waveform and allows seeking via click."""

    position_changed = Signal(float)  # Emits position in seconds when user clicks

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.setMinimumWidth(200)

        # Audio data
        self.samples = None
        self.sample_rate = None
        self.duration = 0.0

        # Playback position (0.0 to 1.0)
        self.playback_position = 0.0

        # Downsampled waveform for display
        self.waveform_peaks = None

        # Colors
        self.bg_color = QColor(40, 40, 40)
        self.waveform_color = QColor(100, 180, 255)
        self.played_color = QColor(60, 140, 200)
        self.cursor_color = QColor(255, 100, 100)
        self.grid_color = QColor(80, 80, 80)

        self.setCursor(Qt.PointingHandCursor)

    def set_audio_data(self, samples, sample_rate):
        """Set audio data and compute waveform for display."""
        self.samples = samples
        self.sample_rate = sample_rate
        self.duration = len(samples) / sample_rate if sample_rate else 0
        self.playback_position = 0.0
        self._compute_waveform()
        self.update()

    def _compute_waveform(self):
        """Downsample audio to create display waveform."""
        if self.samples is None:
            self.waveform_peaks = None
            return

        # Target number of points for display
        target_points = max(self.width(), 400)
        samples_per_point = max(1, len(self.samples) // target_points)

        # Compute peaks for each segment
        num_points = len(self.samples) // samples_per_point
        peaks = []

        for i in range(num_points):
            start = i * samples_per_point
            end = start + samples_per_point
            segment = self.samples[start:end]
            peak = np.max(np.abs(segment)) if len(segment) > 0 else 0
            peaks.append(peak)

        self.waveform_peaks = np.array(peaks)

        # Normalize peaks
        max_peak = np.max(self.waveform_peaks) if len(self.waveform_peaks) > 0 else 1
        if max_peak > 0:
            self.waveform_peaks = self.waveform_peaks / max_peak

    def set_position(self, position_seconds):
        """Set playback position in seconds."""
        if self.duration > 0:
            self.playback_position = min(1.0, max(0.0, position_seconds / self.duration))
        else:
            self.playback_position = 0.0
        self.update()

    def get_position_seconds(self):
        """Get current position in seconds."""
        return self.playback_position * self.duration

    def clear(self):
        """Clear the waveform display."""
        self.samples = None
        self.sample_rate = None
        self.duration = 0.0
        self.playback_position = 0.0
        self.waveform_peaks = None
        self.update()

    def resizeEvent(self, event):
        """Recompute waveform when widget is resized."""
        super().resizeEvent(event)
        if self.samples is not None:
            self._compute_waveform()

    def paintEvent(self, event):
        """Draw the waveform."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        center_y = height // 2

        # Draw background
        painter.fillRect(0, 0, width, height, self.bg_color)

        if self.waveform_peaks is None or len(self.waveform_peaks) == 0:
            # Draw placeholder text
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(self.rect(), Qt.AlignCenter, "No audio loaded")
            return

        # Draw time grid
        self._draw_time_grid(painter, width, height)

        # Draw waveform
        num_points = len(self.waveform_peaks)
        cursor_x = int(self.playback_position * width)

        for i, peak in enumerate(self.waveform_peaks):
            x = int(i * width / num_points)
            bar_height = int(peak * (height - 20) / 2)

            # Color based on whether we've passed this point
            if x < cursor_x:
                painter.setPen(QPen(self.played_color, 1))
            else:
                painter.setPen(QPen(self.waveform_color, 1))

            painter.drawLine(x, center_y - bar_height, x, center_y + bar_height)

        # Draw playback cursor
        painter.setPen(QPen(self.cursor_color, 2))
        painter.drawLine(cursor_x, 0, cursor_x, height)

        # Draw time label at cursor
        current_time = self.playback_position * self.duration
        time_text = self._format_time(current_time)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(cursor_x + 5, 15, time_text)

        # Draw total duration
        duration_text = self._format_time(self.duration)
        painter.drawText(width - 50, height - 5, duration_text)

    def _draw_time_grid(self, painter, width, height):
        """Draw time markers on the waveform."""
        if self.duration <= 0:
            return

        painter.setPen(QPen(self.grid_color, 1, Qt.DashLine))

        # Determine grid interval based on duration
        if self.duration < 10:
            interval = 1.0  # 1 second intervals
        elif self.duration < 60:
            interval = 5.0  # 5 second intervals
        else:
            interval = 10.0  # 10 second intervals

        t = interval
        while t < self.duration:
            x = int(t / self.duration * width)
            painter.drawLine(x, 0, x, height)
            t += interval

    def _format_time(self, seconds):
        """Format time in MM:SS.ms format."""
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}:{secs:05.2f}"

    def mousePressEvent(self, event):
        """Handle click to seek."""
        if event.button() == Qt.LeftButton and self.duration > 0:
            position = event.position().x() / self.width()
            position = min(1.0, max(0.0, position))
            self.playback_position = position
            self.position_changed.emit(position * self.duration)
            self.update()

    def mouseMoveEvent(self, event):
        """Handle drag to seek."""
        if event.buttons() & Qt.LeftButton and self.duration > 0:
            position = event.position().x() / self.width()
            position = min(1.0, max(0.0, position))
            self.playback_position = position
            self.position_changed.emit(position * self.duration)
            self.update()
