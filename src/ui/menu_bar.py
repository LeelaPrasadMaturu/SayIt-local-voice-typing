"""macOS menu bar application using rumps."""

import rumps
from typing import Callable, Optional, List


class MenuBarApp(rumps.App):
    """macOS menu bar application for SayIt."""

    ICON_IDLE = "🎤"
    ICON_RECORDING = "🔴"
    ICON_PROCESSING = "⏳"

    def __init__(
        self,
        hotkey_label: str = "Control + Option + X",
        on_quit: Optional[Callable[[], None]] = None,
        on_settings: Optional[Callable[[], None]] = None,
        on_toggle_mode: Optional[Callable[[str], None]] = None,
        on_model_change: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(
            name="SayIt",
            title=self.ICON_IDLE,
            quit_button=None,
        )

        self._on_quit = on_quit
        self._on_settings = on_settings
        self._on_toggle_mode = on_toggle_mode
        self._on_model_change = on_model_change

        self._current_mode = "push_to_talk"
        self._current_model = "small"
        self._is_recording = False
        self._hotkey_label = hotkey_label

        self._build_menu()

    def _build_menu(self) -> None:
        """Build the menu bar menu."""
        self.menu.clear()

        self.status_item = rumps.MenuItem(f"Ready - Press {self._hotkey_label} to record")
        self.menu.add(self.status_item)

        self.menu.add(rumps.separator)

        mode_menu = rumps.MenuItem("Mode")
        self.ptt_item = rumps.MenuItem(
            "Push to Talk",
            callback=lambda _: self._set_mode("push_to_talk"),
        )
        self.toggle_item = rumps.MenuItem(
            "Toggle",
            callback=lambda _: self._set_mode("toggle"),
        )
        self._update_mode_checkmarks()
        mode_menu.add(self.ptt_item)
        mode_menu.add(self.toggle_item)
        self.menu.add(mode_menu)

        model_menu = rumps.MenuItem("Model")
        self.model_items = {}
        for model in ["tiny", "base", "small", "medium", "large-v3"]:
            item = rumps.MenuItem(
                model,
                callback=lambda sender, m=model: self._set_model(m),
            )
            self.model_items[model] = item
            model_menu.add(item)
        self._update_model_checkmarks()
        self.menu.add(model_menu)

        self.menu.add(rumps.separator)

        self.menu.add(rumps.MenuItem("Settings...", callback=self._open_settings))

        self.menu.add(rumps.separator)

        self.menu.add(rumps.MenuItem("Quit SayIt", callback=self._quit_app))

    def _update_mode_checkmarks(self) -> None:
        """Update checkmarks for mode menu items."""
        self.ptt_item.state = self._current_mode == "push_to_talk"
        self.toggle_item.state = self._current_mode == "toggle"

    def _update_model_checkmarks(self) -> None:
        """Update checkmarks for model menu items."""
        for model, item in self.model_items.items():
            item.state = model == self._current_model

    def _set_mode(self, mode: str) -> None:
        """Set the recording mode."""
        self._current_mode = mode
        self._update_mode_checkmarks()
        if self._on_toggle_mode:
            self._on_toggle_mode(mode)

    def _set_model(self, model: str) -> None:
        """Set the Whisper model."""
        self._current_model = model
        self._update_model_checkmarks()
        if self._on_model_change:
            self._on_model_change(model)

    def _open_settings(self, _) -> None:
        """Open settings window."""
        if self._on_settings:
            self._on_settings()
        else:
            rumps.alert(
                title="Settings",
                message="Edit config at:\n~/.config/sayit/config.toml",
            )

    def _quit_app(self, _) -> None:
        """Quit the application."""
        if self._on_quit:
            self._on_quit()
        rumps.quit_application()

    def set_recording_state(self, recording: bool) -> None:
        """Update the menu bar icon and status for recording state."""
        self._is_recording = recording
        if recording:
            self.title = self.ICON_RECORDING
            self.status_item.title = f"Recording... Release {self._hotkey_label} to stop"
        else:
            self.title = self.ICON_IDLE
            self.status_item.title = f"Ready - Press {self._hotkey_label} to record"

    def set_processing_state(self, processing: bool) -> None:
        """Update the menu bar icon for processing state."""
        if processing:
            self.title = self.ICON_PROCESSING
            self.status_item.title = "Transcribing..."
        else:
            self.title = self.ICON_IDLE
            self.status_item.title = f"Ready - Press {self._hotkey_label} to record"

    def set_mode(self, mode: str) -> None:
        """Set the current mode (called from main app)."""
        self._current_mode = mode
        self._update_mode_checkmarks()

    def set_model(self, model: str) -> None:
        """Set the current model (called from main app)."""
        self._current_model = model
        self._update_model_checkmarks()

    def show_notification(self, title: str, message: str) -> None:
        """Show a notification."""
        rumps.notification(
            title=title,
            subtitle="",
            message=message,
        )

    def show_error(self, message: str) -> None:
        """Show an error notification."""
        rumps.notification(
            title="SayIt Error",
            subtitle="",
            message=message,
        )
