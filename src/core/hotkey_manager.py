"""Global hotkey management using pynput."""

import os
import threading
from typing import Callable, Optional, Set
from pynput import keyboard
from pynput.keyboard import Key, KeyCode


class HotkeyManager:
    """Manages global hotkeys for push-to-talk and toggle modes."""

    DEFAULT_HOTKEY = {Key.ctrl, KeyCode.from_char(".")}

    def __init__(self):
        self._listener: Optional[keyboard.Listener] = None
        self._hotkey: Set = self.DEFAULT_HOTKEY.copy()
        self._current_keys: Set = set()
        self._hotkey_active = False
        self._mode = "push_to_talk"
        self._debug_enabled = os.environ.get("WHISPERFLOW_DEBUG", "0").lower() not in {
            "0",
            "false",
            "no",
            "off",
        }

        self.on_hotkey_press: Optional[Callable[[], None]] = None
        self.on_hotkey_release: Optional[Callable[[], None]] = None

        self._running = False
        self._lock = threading.Lock()

    def _debug_log(self, message: str) -> None:
        """Print a debug message when debug logging is enabled."""
        if self._debug_enabled:
            print(f"[debug][hotkey] {message}", flush=True)

    def _normalize_key(self, key) -> Optional:
        """Normalize a key to a comparable format."""
        if isinstance(key, Key):
            if key in (Key.alt, Key.alt_l, Key.alt_r):
                return Key.alt
            if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
                return Key.ctrl
            if key in (Key.shift, Key.shift_l, Key.shift_r):
                return Key.shift
            if key in (Key.cmd, Key.cmd_l, Key.cmd_r):
                return Key.cmd
            return key
        if isinstance(key, KeyCode):
            if key.char:
                return KeyCode.from_char(key.char.lower())
            return key
        return None

    def _on_press(self, key) -> None:
        """Handle key press events."""
        normalized = self._normalize_key(key)
        if normalized is None:
            return

        with self._lock:
            was_already_down = normalized in self._current_keys
            self._current_keys.add(normalized)
            if self._is_hotkey_key(normalized) and not was_already_down:
                self._debug_log(
                    f"key pressed: {self._format_key(normalized)}; "
                    f"down={self._format_keys(self._current_keys)}"
                )
            
            if self._check_hotkey_match():
                if not self._hotkey_active:
                    self._hotkey_active = True
                    self._debug_log("hotkey matched; firing press callback")
                    if self.on_hotkey_press:
                        threading.Thread(target=self.on_hotkey_press, daemon=True).start()

    def _on_release(self, key) -> None:
        """Handle key release events."""
        normalized = self._normalize_key(key)
        if normalized is None:
            return

        with self._lock:
            was_hotkey_key = self._is_hotkey_key(normalized)
            self._current_keys.discard(normalized)
            if was_hotkey_key:
                self._debug_log(
                    f"key released: {self._format_key(normalized)}; "
                    f"down={self._format_keys(self._current_keys)}"
                )
            
            if self._hotkey_active and self._mode == "push_to_talk":
                if not self._check_hotkey_match():
                    self._hotkey_active = False
                    self._debug_log("hotkey released; firing release callback")
                    if self.on_hotkey_release:
                        threading.Thread(target=self.on_hotkey_release, daemon=True).start()

    def _check_hotkey_match(self) -> bool:
        """Check if current keys match the hotkey combination."""
        normalized_hotkey = set()
        for k in self._hotkey:
            n = self._normalize_key(k)
            if n:
                normalized_hotkey.add(n)

        normalized_current = set()
        for k in self._current_keys:
            n = self._normalize_key(k)
            if n:
                normalized_current.add(n)

        return normalized_hotkey.issubset(normalized_current)

    def _is_hotkey_key(self, key) -> bool:
        """Check whether a key is part of the configured hotkey."""
        return self._normalize_key(key) in {
            self._normalize_key(hotkey_key) for hotkey_key in self._hotkey
        }

    def start(self) -> None:
        """Start listening for hotkeys."""
        if self._running:
            return

        self._running = True
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()
        self._debug_log(
            f"listener started; hotkey={self._format_keys(self._hotkey)}; mode={self._mode}"
        )

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._debug_log("listener stopped")

    def set_hotkey(self, keys: Set) -> None:
        """Set the hotkey combination.
        
        Args:
            keys: Set of keys that form the hotkey (e.g., {Key.alt, KeyCode.from_char(' ')})
        """
        with self._lock:
            self._hotkey = keys
            self._hotkey_active = False
        self._debug_log(f"hotkey set to {self._format_keys(keys)}")

    def set_mode(self, mode: str) -> None:
        """Set the hotkey mode.
        
        Args:
            mode: Either "push_to_talk" or "toggle"
        """
        if mode not in ("push_to_talk", "toggle"):
            raise ValueError("Mode must be 'push_to_talk' or 'toggle'")
        self._mode = mode
        self._debug_log(f"mode set to {mode}")

    def reset_state(self) -> None:
        """Reset the hotkey state (for toggle mode)."""
        with self._lock:
            self._hotkey_active = False
        self._debug_log("hotkey state reset")

    @property
    def mode(self) -> str:
        """Get the current hotkey mode."""
        return self._mode

    @property
    def is_running(self) -> bool:
        """Check if the listener is running."""
        return self._running

    @staticmethod
    def parse_hotkey_string(hotkey_str: str) -> Set:
        """Parse a hotkey string like 'ctrl+option+x' into a key set.
        
        Args:
            hotkey_str: String like "ctrl+option+x", "ctrl+shift+r", etc.
            
        Returns:
            Set of Key and KeyCode objects
        """
        key_map = {
            "alt": Key.alt,
            "option": Key.alt,
            "ctrl": Key.ctrl,
            "control": Key.ctrl,
            "shift": Key.shift,
            "cmd": Key.cmd,
            "command": Key.cmd,
            "space": KeyCode.from_char(" "),
            "enter": Key.enter,
            "return": Key.enter,
            "tab": Key.tab,
            "esc": Key.esc,
            "escape": Key.esc,
        }
        for number in range(1, 21):
            key_name = f"f{number}"
            if hasattr(Key, key_name):
                key_map[key_name] = getattr(Key, key_name)

        keys = set()
        parts = hotkey_str.lower().replace(" ", "").split("+")

        for part in parts:
            if part in key_map:
                keys.add(key_map[part])
            elif len(part) == 1:
                keys.add(KeyCode.from_char(part))
            else:
                print(f"Unknown key: {part}")

        return keys

    @staticmethod
    def format_hotkey_label(hotkey_str: str) -> str:
        """Format a config hotkey string for user-facing text."""
        label_map = {
            "alt": "Option",
            "option": "Option",
            "ctrl": "Control",
            "control": "Control",
            "shift": "Shift",
            "cmd": "Command",
            "command": "Command",
            "space": "Space",
            "enter": "Enter",
            "return": "Return",
            "tab": "Tab",
            "esc": "Esc",
            "escape": "Esc",
        }
        parts = hotkey_str.lower().replace(" ", "").split("+")
        labels = [
            label_map.get(part, part.upper() if part.startswith("f") else part.upper())
            for part in parts
            if part
        ]
        return " + ".join(labels)

    @staticmethod
    def _format_key(key) -> str:
        """Format pynput keys for debug logs."""
        if key in (Key.alt, Key.alt_l, Key.alt_r):
            return "Option"
        if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
            return "Control"
        if key in (Key.shift, Key.shift_l, Key.shift_r):
            return "Shift"
        if key in (Key.cmd, Key.cmd_l, Key.cmd_r):
            return "Command"
        if key == KeyCode.from_char(" "):
            return "Space"
        if isinstance(key, KeyCode) and key.char:
            return key.char.upper()
        label = str(key).replace("Key.", "")
        return label.upper() if label.startswith("f") else label

    @staticmethod
    def _format_keys(keys: Set) -> str:
        """Format a set of pynput keys for debug logs."""
        if not keys:
            return "(none)"
        return " + ".join(HotkeyManager._format_key(key) for key in keys)
