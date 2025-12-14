import os
from typing import Optional

import dearpygui.dearpygui as dpg
import numpy as np
from parakeet_lipsync.audio_player import AudioPlayer
from parakeet_lipsync.recognizer import PhonemeRecognizer, export_moho_timesheet


class ParakeetApp:
    """Main application class for Parakeet Lipsync."""

    def __init__(self):
        self.audio_player = AudioPlayer()
        self.recognizer = PhonemeRecognizer()

        self.current_file: Optional[str] = None
        self.lipsync_data: str = ""
        self.fps: int = 24

        # Waveform data
        self.waveform_x: list = []
        self.waveform_y: list = []
        self.cursor_position: float = 0.0
        self._play_to_target: Optional[float] = None  # Target for "play to cursor"

        # Parsed lipsync data for mouth shape display
        self._lipsync_entries: list[tuple[float, float, str]] = []  # (start, duration, shape)

        # UI element tags
        self.file_label_tag = "file_label"
        self.waveform_plot_tag = "waveform_plot"
        self.waveform_series_tag = "waveform_series"
        self.cursor_line_tag = "cursor_line"
        self.output_text_tag = "output_text"
        self.fps_input_tag = "fps_input"
        self.process_btn_tag = "process_btn"
        self.play_btn_tag = "play_btn"

        # Set up audio player callbacks
        self.audio_player.set_position_callback(self._on_position_update)
        self.audio_player.set_finished_callback(self._on_playback_finished)

    def run(self):
        """Run the application."""
        dpg.create_context()
        self._setup_ui()
        self._setup_theme()

        dpg.create_viewport(title="Parakeet Lipsync", width=1000, height=700)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    def _setup_theme(self):
        """Set up application theme."""
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
        dpg.bind_theme(global_theme)

    def _setup_ui(self):
        """Set up the user interface."""
        # File dialog for opening audio
        with dpg.file_dialog(
                directory_selector=False,
                show=False,
                callback=self._on_file_selected,
                tag="file_dialog",
                width=600,
                height=400
        ):
            dpg.add_file_extension(".wav", color=(0, 255, 0, 255))
            dpg.add_file_extension(".mp3", color=(0, 255, 255, 255))
            dpg.add_file_extension(".*")

        # Save file dialogs
        with dpg.file_dialog(
                directory_selector=False,
                show=False,
                callback=self._on_save_text,
                tag="save_text_dialog",
                width=600,
                height=400,
                default_filename="lipsync_output.txt"
        ):
            dpg.add_file_extension(".txt", color=(255, 255, 0, 255))

        with dpg.file_dialog(
                directory_selector=False,
                show=False,
                callback=self._on_save_moho,
                tag="save_moho_dialog",
                width=600,
                height=400,
                default_filename="lipsync_output.dat"
        ):
            dpg.add_file_extension(".dat", color=(255, 128, 0, 255))

        # Register keyboard shortcuts
        with dpg.handler_registry():
            dpg.add_key_press_handler(dpg.mvKey_O, callback=self._shortcut_open)
            dpg.add_key_press_handler(dpg.mvKey_S, callback=self._shortcut_save)
            dpg.add_key_press_handler(dpg.mvKey_Spacebar, callback=self._shortcut_play_pause)

        # Main window
        with dpg.window(tag="main_window"):
            # Menu bar
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    dpg.add_menu_item(
                        label="Open Audio (Ctrl+O)",
                        callback=lambda: dpg.show_item("file_dialog")
                    )
                    dpg.add_separator()
                    dpg.add_menu_item(
                        label="Save Output (Ctrl+S)",
                        callback=lambda: dpg.show_item("save_text_dialog"),
                        tag="save_menu_item",
                        enabled=False
                    )
                    dpg.add_menu_item(
                        label="Export Moho Timesheet",
                        callback=lambda: dpg.show_item("save_moho_dialog"),
                        tag="export_menu_item",
                        enabled=False
                    )
                    dpg.add_separator()
                    dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())

                with dpg.menu(label="Help"):
                    dpg.add_menu_item(label="About", callback=self._show_about)

            # Top controls row
            with dpg.group(horizontal=True):
                dpg.add_text("FPS:")
                dpg.add_input_int(
                    tag=self.fps_input_tag,
                    default_value=24,
                    min_value=12,
                    max_value=60,
                    width=80,
                    callback=self._on_fps_changed
                )
                dpg.add_spacer(width=20)
                dpg.add_text("No audio loaded. Press Ctrl+O to open.", tag=self.file_label_tag)

            dpg.add_spacer(height=10)

            # Waveform plot
            with dpg.plot(
                    tag=self.waveform_plot_tag,
                    height=150,
                    width=-1,
                    no_menus=True,
                    no_box_select=True,
                    no_mouse_pos=True
            ):
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="waveform_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="", tag="waveform_y_axis", no_tick_labels=True)
                dpg.set_axis_limits("waveform_y_axis", -1.1, 1.1)

                # Placeholder waveform
                dpg.add_line_series(
                    [0], [0],
                    parent="waveform_y_axis",
                    tag=self.waveform_series_tag
                )
                # Cursor line
                dpg.add_vline_series(
                    [0],
                    parent="waveform_y_axis",
                    tag=self.cursor_line_tag
                )

            # Set up plot click handler
            with dpg.item_handler_registry(tag="plot_handler"):
                dpg.add_item_clicked_handler(callback=self._on_waveform_click)
            dpg.bind_item_handler_registry(self.waveform_plot_tag, "plot_handler")

            dpg.add_spacer(height=10)

            # Playback controls
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Play",
                    tag=self.play_btn_tag,
                    callback=self._on_play_pause,
                    width=80,
                    enabled=False
                )
                dpg.add_button(
                    label="Stop",
                    callback=self._on_stop,
                    width=80,
                    enabled=False,
                    tag="stop_btn"
                )
                dpg.add_button(
                    label="Play to Cursor",
                    callback=self._on_play_to_cursor,
                    width=120,
                    enabled=False,
                    tag="play_to_btn"
                )
                dpg.add_button(
                    label="Play from Cursor",
                    callback=self._on_play_from_cursor,
                    width=120,
                    enabled=False,
                    tag="play_from_btn"
                )
                dpg.add_spacer(width=20)
                dpg.add_text("0:00.00 / 0:00.00", tag="time_display")

            dpg.add_spacer(height=10)

            # Process button
            dpg.add_button(
                label="Process Audio",
                tag=self.process_btn_tag,
                callback=self._on_process,
                width=-1,
                height=40,
                enabled=False
            )

            dpg.add_spacer(height=10)

            # Output section: text area on left, mouth shape on right
            dpg.add_text("Output:")
            with dpg.group(horizontal=True):
                # Text area (takes most of the width)
                dpg.add_input_text(
                    tag=self.output_text_tag,
                    multiline=True,
                    readonly=True,
                    width=-200,
                    height=-1,
                    default_value="Load an audio file and click 'Process Audio' to generate lipsync data."
                )

                # Mouth shape display panel
                with dpg.child_window(width=-1, height=-1, border=True, tag="mouth_shape_panel"):
                    dpg.add_text("Mouth Shape", color=(150, 150, 150))
                    dpg.add_separator()
                    dpg.add_spacer(height=30)
                    # Large mouth shape text
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=40)
                        dpg.add_text(
                            "",
                            tag="mouth_shape_display",
                            color=(100, 200, 255)
                        )
                    dpg.add_spacer(height=15)
                    dpg.add_text(
                        "Not processed",
                        tag="mouth_shape_time",
                        color=(150, 150, 150)
                    )

    def _on_file_selected(self, sender, app_data):
        """Handle file selection."""
        if app_data and "file_path_name" in app_data:
            file_path = app_data["file_path_name"]
            self._load_audio(file_path)

    def _load_audio(self, file_path: str):
        """Load audio file and update UI."""
        try:
            samples, sample_rate = self.audio_player.load(file_path)
            self.current_file = file_path
            self.cursor_position = 0.0

            # Clear previous lipsync data
            self.lipsync_data = ""
            self._lipsync_entries = []
            dpg.set_value("mouth_shape_display", "")
            dpg.set_value("mouth_shape_time", "Not processed")

            # Update file label
            filename = os.path.basename(file_path)
            dpg.set_value(self.file_label_tag, f"Loaded: {filename}")

            # Generate waveform data (downsample for display)
            self._update_waveform(samples, sample_rate)

            # Enable controls
            dpg.configure_item(self.process_btn_tag, enabled=True)
            dpg.configure_item(self.play_btn_tag, enabled=True)
            dpg.configure_item("stop_btn", enabled=True)
            dpg.configure_item("play_to_btn", enabled=True)
            dpg.configure_item("play_from_btn", enabled=True)

            # Update time display
            self._update_time_display()

            print(f"Loaded: {file_path}")
        except Exception as e:
            print(f"Error loading audio: {e}")
            dpg.set_value(self.file_label_tag, f"Error loading file: {e}")

    def _update_waveform(self, samples: np.ndarray, sample_rate: int):
        """Update waveform display."""
        duration = len(samples) / sample_rate

        # Downsample for display (target ~2000 points)
        target_points = 2000
        step = max(1, len(samples) // target_points)

        # Use peak values for better visualization
        num_points = len(samples) // step
        self.waveform_x = []
        self.waveform_y = []

        for i in range(num_points):
            start_idx = i * step
            end_idx = min(start_idx + step, len(samples))
            segment = samples[start_idx:end_idx]

            t = (start_idx / sample_rate)
            peak = np.max(np.abs(segment)) if len(segment) > 0 else 0

            # Add positive and negative peaks for waveform shape
            self.waveform_x.extend([t, t])
            self.waveform_y.extend([-peak, peak])

        # Update plot
        dpg.set_value(self.waveform_series_tag, [self.waveform_x, self.waveform_y])
        dpg.set_axis_limits("waveform_x_axis", 0, duration)
        dpg.fit_axis_data("waveform_x_axis")

    def _on_waveform_click(self, sender, app_data):
        """Handle waveform click for seeking."""
        if self.audio_player.duration <= 0:
            return

        # Get mouse position relative to plot
        mouse_pos = dpg.get_plot_mouse_pos()
        if mouse_pos:
            click_time = mouse_pos[0]
            click_time = max(0, min(click_time, self.audio_player.duration))

            self.cursor_position = click_time
            self.audio_player.seek(click_time)
            self._update_cursor()
            self._update_time_display()

    def _update_cursor(self):
        """Update cursor position on waveform."""
        dpg.set_value(self.cursor_line_tag, [[self.cursor_position], []])

    def _update_time_display(self, position: Optional[float] = None):
        """Update time display label."""
        current = position if position is not None else self.cursor_position
        total = self.audio_player.duration

        current_str = f"{int(current // 60)}:{current % 60:05.2f}"
        total_str = f"{int(total // 60)}:{total % 60:05.2f}"
        dpg.set_value("time_display", f"{current_str} / {total_str}")

    def _on_position_update(self, position: float):
        """Handle position update from audio player."""
        # Don't update cursor when in "play to" mode - show target instead
        if self._play_to_target is None:
            self.cursor_position = position
            self._update_cursor()
        self._update_time_display(position)
        self._update_mouth_shape_display(position)

    def _on_playback_finished(self):
        """Handle playback finished."""
        # If we were in "play to" mode, move cursor to the target position
        if self._play_to_target is not None:
            self.cursor_position = self._play_to_target
            self._update_cursor()
            self._play_to_target = None
        dpg.configure_item(self.play_btn_tag, label="Play")

    def _on_play_pause(self):
        """Toggle playback."""
        if self.audio_player.is_playing:
            self.audio_player.pause()
            self._play_to_target = None
            dpg.configure_item(self.play_btn_tag, label="Play")
        else:
            self.audio_player.play()
            dpg.configure_item(self.play_btn_tag, label="Pause")

    def _on_stop(self):
        """Stop playback and reset."""
        self.audio_player.stop()
        self.audio_player.current_position = 0
        self.cursor_position = 0.0
        self._play_to_target = None
        self._update_cursor()
        self._update_time_display()
        dpg.configure_item(self.play_btn_tag, label="Play")

    def _on_play_to_cursor(self):
        """Play from start to cursor position."""
        if self.cursor_position > 0:
            self._play_to_target = self.cursor_position  # Remember target
            self.audio_player.play_to(self.cursor_position)
            dpg.configure_item(self.play_btn_tag, label="Pause")

    def _on_play_from_cursor(self):
        """Play from cursor position to end."""
        self._play_to_target = None  # Clear any "play to" target
        self.audio_player.play_from(self.cursor_position)
        dpg.configure_item(self.play_btn_tag, label="Pause")

    def _on_fps_changed(self, sender, app_data):
        """Handle FPS change."""
        self.fps = app_data

    def _on_process(self):
        """Process audio for phoneme recognition."""
        if not self.current_file:
            return

        dpg.configure_item(self.process_btn_tag, enabled=False, label="Processing...")
        dpg.set_value(self.output_text_tag, "Processing audio... Please wait.")

        def on_complete(result: str):
            self.lipsync_data = result
            self._parse_lipsync_data(result)
            dpg.set_value(self.output_text_tag, result)
            dpg.configure_item(self.process_btn_tag, enabled=True, label="Process Audio")
            dpg.configure_item("save_menu_item", enabled=True)
            dpg.configure_item("export_menu_item", enabled=True)
            print("Processing complete.")

        def on_error(error: Exception):
            dpg.set_value(self.output_text_tag, f"Error: {error}")
            dpg.configure_item(self.process_btn_tag, enabled=True, label="Process Audio")
            print(f"Processing error: {error}")

        self.recognizer.recognize_async(self.current_file, on_complete, on_error)

    def _on_save_text(self, sender, app_data):
        """Save lipsync output as text file."""
        if app_data and "file_path_name" in app_data:
            file_path = app_data["file_path_name"]
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.lipsync_data)
                print(f"Saved to: {file_path}")
            except Exception as e:
                print(f"Error saving file: {e}")

    def _on_save_moho(self, sender, app_data):
        """Export lipsync data as Moho timesheet."""
        if app_data and "file_path_name" in app_data:
            file_path = app_data["file_path_name"]
            try:
                moho_data = export_moho_timesheet(self.lipsync_data, self.fps)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(moho_data)
                print(f"Exported to: {file_path}")
            except Exception as e:
                print(f"Error exporting file: {e}")

    def _is_ctrl_down(self) -> bool:
        """Check if either Ctrl key is pressed."""
        return dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl)

    def _shortcut_open(self, sender, app_data):
        """Handle Ctrl+O shortcut."""
        if self._is_ctrl_down():
            dpg.show_item("file_dialog")

    def _shortcut_save(self, sender, app_data):
        """Handle Ctrl+S shortcut."""
        if self._is_ctrl_down() and self.lipsync_data:
            dpg.show_item("save_text_dialog")

    def _shortcut_play_pause(self, sender, app_data):
        """Handle Space shortcut for play/pause."""
        if self.current_file:
            self._on_play_pause()

    def _parse_lipsync_data(self, data: str) -> None:
        """Parse lipsync data string into list of entries."""
        self._lipsync_entries = []
        for line in data.strip().split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        start_time = float(parts[0])
                        duration = float(parts[1])
                        mouth_shape = parts[2]
                        self._lipsync_entries.append((start_time, duration, mouth_shape))
                    except ValueError:
                        continue

    def _get_mouth_shape_at(self, position: float) -> tuple[str, float, float] | None:
        """Get the mouth shape at a given position.

        Returns: (shape, start_time, end_time) or None if no shape at position.
        """
        for start_time, duration, shape in self._lipsync_entries:
            end_time = start_time + duration
            if start_time <= position < end_time:
                return (shape, start_time, end_time)
        return None

    def _update_mouth_shape_display(self, position: float) -> None:
        """Update the mouth shape display widget."""
        if not self._lipsync_entries:
            dpg.set_value("mouth_shape_display", "")
            dpg.set_value("mouth_shape_time", "Not processed")
            return

        result = self._get_mouth_shape_at(position)
        if result:
            shape, start_time, end_time = result
            dpg.set_value("mouth_shape_display", shape)
            dpg.set_value("mouth_shape_time", f"{start_time:.2f}s - {end_time:.2f}s")
        else:
            dpg.set_value("mouth_shape_display", "rest")
            dpg.set_value("mouth_shape_time", "")

    def _show_about(self):
        """Show about dialog."""
        with dpg.window(label="About", modal=True, width=300, height=150, no_resize=True):
            dpg.add_text("Parakeet Lipsync")
            dpg.add_text("Version 0.1.0")
            dpg.add_spacer(height=10)
            dpg.add_text("A lip-syncing application using")
            dpg.add_text("phoneme recognition with Allosaurus.")
            dpg.add_spacer(height=10)
            dpg.add_button(label="Close", callback=lambda s, a, u: dpg.delete_item(u), user_data=dpg.last_container())
