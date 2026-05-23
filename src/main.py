"""SayIt - Main application entry point."""

import os
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from core.audio_recorder import AudioRecorder
from core.whisper_engine import WhisperEngine
from core.text_inserter import TextInserter
from core.hotkey_manager import HotkeyManager
from utils.config import Config
from ui.menu_bar import MenuBarApp


class SayItApp:
    """Main SayIt application orchestrating all components."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load()
        self._debug_enabled = os.environ.get("SAYIT_DEBUG", "0").lower() not in {
            "0",
            "false",
            "no",
            "off",
        }
        self._debug_log("initializing app components")

        self.audio_recorder = AudioRecorder(
            sample_rate=self.config.audio.sample_rate,
            channels=self.config.audio.channels,
            device=self.config.audio.device_id,
        )

        self.whisper_engine = WhisperEngine(
            model_name=self.config.whisper.model,
            device=self.config.whisper.device,
            compute_type=self.config.whisper.compute_type,
            language=self.config.whisper.language,
        )

        self.text_inserter = TextInserter(
            use_clipboard=True,
        )

        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.set_hotkey(
            HotkeyManager.parse_hotkey_string(self.config.hotkey.hotkey)
        )
        self.hotkey_manager.set_mode(self.config.hotkey.mode)

        self.menu_app: Optional[MenuBarApp] = None

        self._setup_callbacks()

        self._is_processing = False
        self._lock = threading.Lock()
        self._debug_log("app initialized")

    def _debug_log(self, message: str) -> None:
        """Print a debug message when debug logging is enabled."""
        if self._debug_enabled:
            print(f"[debug][app] {message}", flush=True)

    def _setup_callbacks(self) -> None:
        """Set up callbacks between components."""
        self.hotkey_manager.on_hotkey_press = self._on_hotkey_press
        self.hotkey_manager.on_hotkey_release = self._on_hotkey_release

        self.audio_recorder.on_recording_start = self._on_recording_start
        self.audio_recorder.on_recording_stop = self._on_recording_stop

    def _on_hotkey_press(self) -> None:
        """Called when hotkey is pressed."""
        self._debug_log("hotkey press callback received")
        
        with self._lock:
            if self._is_processing:
                self._debug_log("hotkey press ignored because transcription is processing")
                return
            if self.audio_recorder.is_active:
                self._debug_log("hotkey press ignored because recorder is already active")
                return

        if self.hotkey_manager.mode == "toggle":
            if self.audio_recorder.is_recording:
                self._debug_log("toggle mode: hotkey pressed while recording; stopping")
                self._stop_and_transcribe()
            else:
                self._debug_log("toggle mode: hotkey pressed while idle; starting recording")
                self.audio_recorder.start_recording()
        else:
            self._debug_log("push-to-talk mode: starting recording")
            self.audio_recorder.start_recording()

    def _on_hotkey_release(self) -> None:
        """Called when hotkey is released (push-to-talk mode)."""
        self._debug_log("hotkey release callback received")
        if self.hotkey_manager.mode == "push_to_talk":
            # Wait briefly for recording to actually start (race condition fix)
            for _ in range(10):
                if self.audio_recorder.is_recording:
                    break
                time.sleep(0.05)
            
            if self.audio_recorder.is_recording:
                self._debug_log("push-to-talk mode: stopping recording after release")
                self._stop_and_transcribe()
            else:
                self._debug_log("release ignored because recorder is not active")

    def _stop_and_transcribe(self) -> None:
        """Stop recording and start transcription."""
        self._debug_log("stop requested; saving recorded audio")
        audio_path = self.audio_recorder.stop_recording()
        if audio_path:
            self._debug_log(f"audio captured at {audio_path}; starting processing thread")
            threading.Thread(
                target=self._transcribe_and_insert,
                args=(audio_path,),
                daemon=True,
            ).start()
        else:
            self._debug_log("no audio file produced; skipping transcription")

    def _on_recording_start(self) -> None:
        """Called when recording starts."""
        self._debug_log("recorder state changed: recording started")
        print("🎤 Recording started...")
        if self.menu_app:
            self.menu_app.set_recording_state(True)

    def _on_recording_stop(self, audio_path: str) -> None:
        """Called when recording stops."""
        self._debug_log(f"recorder state changed: recording stopped; file={audio_path}")
        print(f"⏹️  Recording stopped: {audio_path}")
        if self.menu_app:
            self.menu_app.set_recording_state(False)

    def _transcribe_and_insert(self, audio_path: str) -> None:
        """Transcribe audio and insert text at cursor."""
        with self._lock:
            if self._is_processing:
                self._debug_log("processing request ignored because another one is active")
                return
            self._is_processing = True

        try:
            self._debug_log("processing now: transcribing audio")
            if self.menu_app:
                self.menu_app.set_processing_state(True)

            print("🔄 Transcribing...")
            result = self.whisper_engine.transcribe(audio_path)
            self._debug_log(
                f"transcription finished: language={result.language}, "
                f"duration={result.duration:.2f}s, chars={len(result.text)}"
            )

            if result.text:
                text = result.text.strip()
                if self.config.output.add_trailing_space:
                    text += " "

                print(f"📝 Transcribed: {text}")

                time.sleep(0.1)

                self._debug_log("inserting transcribed text at current cursor")
                success = self.text_inserter.insert_text(text)
                if success:
                    self._debug_log("text insertion succeeded")
                    print("✅ Text inserted at cursor")
                else:
                    self._debug_log("text insertion failed")
                    print("❌ Failed to insert text")
                    if self.menu_app:
                        self.menu_app.show_error("Failed to insert text")
            else:
                self._debug_log("transcription returned empty text")
                print("⚠️  No speech detected")

        except Exception as e:
            self._debug_log(f"error during processing: {e}")
            print(f"❌ Error: {e}")
            if self.menu_app:
                self.menu_app.show_error(str(e))

        finally:
            self._debug_log("processing complete; cleaning up temp audio")
            self._is_processing = False
            if self.menu_app:
                self.menu_app.set_processing_state(False)

            try:
                os.unlink(audio_path)
            except Exception:
                pass

    def _on_mode_change(self, mode: str) -> None:
        """Called when mode is changed from menu."""
        self._debug_log(f"mode changed from menu: {mode}")
        self.hotkey_manager.set_mode(mode)
        self.config.hotkey.mode = mode
        print(f"Mode changed to: {mode}")

    def _on_model_change(self, model: str) -> None:
        """Called when model is changed from menu."""
        self._debug_log(f"model changed from menu: {model}")
        self.whisper_engine.change_model(model)
        self.config.whisper.model = model
        print(f"Model changed to: {model}")

        threading.Thread(
            target=self.whisper_engine.load_model,
            daemon=True,
        ).start()

    def _on_quit(self) -> None:
        """Called when app is quit."""
        self._debug_log("quit requested; stopping listeners and saving config")
        print("Shutting down SayIt...")
        self.hotkey_manager.stop()
        self.audio_recorder.cleanup()
        self.config.save()
        self._remove_pid_file()

    @staticmethod
    def _remove_pid_file() -> None:
        """Remove PID file on shutdown."""
        pid_file = Path(__file__).resolve().parent.parent / ".sayit.pid"
        try:
            pid_file.unlink(missing_ok=True)
        except OSError:
            pass

    def preload_model(self) -> None:
        """Preload the Whisper model in background."""
        def load():
            self._debug_log("model preload started")
            print(f"Preloading Whisper model '{self.config.whisper.model}'...")
            self.whisper_engine.load_model()
            self._debug_log("model preload finished")
            print("Model ready!")

        threading.Thread(target=load, daemon=True).start()

    def run(self) -> None:
        """Run the application."""
        hotkey_label = HotkeyManager.format_hotkey_label(self.config.hotkey.hotkey)

        print("=" * 50)
        print("  SayIt Local - Voice Typing")
        print("=" * 50)
        print(f"  Hotkey: {hotkey_label}")
        print(f"  Mode: {self.config.hotkey.mode}")
        print(f"  Model: {self.config.whisper.model}")
        print("=" * 50)

        self.hotkey_manager.start()
        self._debug_log("started listening for global hotkey")
        print("✓ Hotkey listener started")

        self.preload_model()

        self.menu_app = MenuBarApp(
            hotkey_label=hotkey_label,
            on_quit=self._on_quit,
            on_toggle_mode=self._on_mode_change,
            on_model_change=self._on_model_change,
        )
        self.menu_app.set_mode(self.config.hotkey.mode)
        self.menu_app.set_model(self.config.whisper.model)

        print("✓ Menu bar app started")
        print(f"\nSayIt is ready! Press {hotkey_label} to start recording.\n")

        self.menu_app.run()


def main():
    """Main entry point."""
    config = Config.load()
    
    app = SayItApp(config)
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        app._on_quit()


if __name__ == "__main__":
    main()
