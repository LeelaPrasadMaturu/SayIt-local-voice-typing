"""Text insertion module - types text at cursor position."""

import time
from typing import Optional
from pynput.keyboard import Controller, Key
import pyperclip


class TextInserter:
    """Inserts text at the current cursor position using clipboard paste."""

    def __init__(
        self,
        use_clipboard: bool = True,
    ):
        """Initialize the text inserter.
        
        Args:
            use_clipboard: Kept for compatibility. Clipboard paste is always used.
        """
        self.use_clipboard = True
        self._keyboard = Controller()

    def insert_text(self, text: str) -> bool:
        """Insert text at the current cursor position.
        
        Args:
            text: The text to insert
            
        Returns:
            True if successful, False otherwise
        """
        if not text:
            return False

        try:
            return self._insert_via_clipboard(text)
        except Exception as e:
            print(f"Error inserting text: {e}")
            return False

    def _insert_via_clipboard(self, text: str) -> bool:
        """Insert text via clipboard paste (Cmd+V on macOS)."""
        try:
            old_clipboard = None
            try:
                old_clipboard = pyperclip.paste()
            except Exception:
                pass

            pyperclip.copy(text)
            
            time.sleep(0.05)

            with self._keyboard.pressed(Key.cmd):
                self._keyboard.press("v")
                self._keyboard.release("v")

            # Rich editors like Slack and Notes may process paste asynchronously.
            time.sleep(0.35)

            if old_clipboard is not None:
                try:
                    pyperclip.copy(old_clipboard)
                except Exception:
                    pass

            return True
        except Exception as e:
            print(f"Clipboard paste failed: {e}")
            return False

    def press_key(self, key: Key) -> None:
        """Press a special key."""
        self._keyboard.press(key)
        self._keyboard.release(key)

    def press_enter(self) -> None:
        """Press Enter key."""
        self.press_key(Key.enter)

    def press_space(self) -> None:
        """Press Space key."""
        self.press_key(Key.space)

    def set_typing_mode(self, use_clipboard: bool) -> None:
        """Kept for compatibility. Clipboard paste is mandatory."""
        self.use_clipboard = True

    def set_typing_delay(self, delay: float) -> None:
        """Kept for compatibility. Direct typing is disabled."""
        return None
