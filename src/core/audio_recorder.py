"""Audio recording module using sounddevice."""

import os
import threading
import tempfile
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as write_wav
from pathlib import Path
from typing import Callable, Optional


class AudioRecorder:
    """Records audio from microphone with push-to-talk or toggle support."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype: str = "float32",
        device: Optional[int] = None,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.device = device

        self._recording = False
        self._starting = False  # Prevents race condition during startup
        self._audio_chunks: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._state_lock = threading.Lock()  # Protects _recording and _starting
        self._chunks_lock = threading.Lock()  # Protects _audio_chunks

        self._debug = os.environ.get("WHISPERFLOW_DEBUG", "0").lower() not in {"0", "false", "no", "off"}

        self.on_recording_start: Optional[Callable[[], None]] = None
        self.on_recording_stop: Optional[Callable[[str], None]] = None

    def _debug_log(self, msg: str) -> None:
        if self._debug:
            print(f"[debug][recorder] {msg}", flush=True)

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        with self._state_lock:
            return self._recording

    @property
    def is_active(self) -> bool:
        """Check if recording or about to record (for race condition handling)."""
        with self._state_lock:
            return self._recording or self._starting

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Callback for audio stream - stores audio chunks."""
        if status:
            self._debug_log(f"audio status: {status}")
        if self._recording:
            with self._chunks_lock:
                self._audio_chunks.append(indata.copy())

    def start_recording(self) -> bool:
        """Start recording audio.
        
        Returns:
            True if recording started, False if already recording or failed.
        """
        with self._state_lock:
            if self._recording or self._starting:
                self._debug_log("start_recording called but already recording/starting")
                return False
            self._starting = True

        self._debug_log("start_recording: initializing stream")

        try:
            with self._chunks_lock:
                self._audio_chunks = []

            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                device=self.device,
                callback=self._audio_callback,
            )
            self._stream.start()

            with self._state_lock:
                self._recording = True
                self._starting = False

            self._debug_log("start_recording: stream started successfully")

            if self.on_recording_start:
                self.on_recording_start()

            return True

        except Exception as e:
            self._debug_log(f"start_recording failed: {e}")
            with self._state_lock:
                self._starting = False
                self._recording = False
            return False

    def stop_recording(self) -> Optional[str]:
        """Stop recording and save to temporary WAV file.
        
        Returns:
            Path to the temporary WAV file, or None if no audio recorded.
        """
        with self._state_lock:
            if not self._recording:
                self._debug_log("stop_recording called but not recording")
                return None
            self._recording = False

        self._debug_log("stop_recording: stopping stream")

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                self._debug_log(f"error closing stream: {e}")
            self._stream = None

        with self._chunks_lock:
            if not self._audio_chunks:
                self._debug_log("stop_recording: no audio chunks captured")
                return None

            audio_data = np.concatenate(self._audio_chunks, axis=0)
            self._audio_chunks = []

        self._debug_log(f"stop_recording: captured {len(audio_data)} samples ({len(audio_data)/self.sample_rate:.2f}s)")

        if len(audio_data) < self.sample_rate * 0.3:  # At least 0.3 seconds
            self._debug_log("stop_recording: audio too short, discarding")
            return None

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False, prefix="sayit_"
        )
        temp_path = temp_file.name
        temp_file.close()

        audio_int16 = (audio_data * 32767).astype(np.int16)
        write_wav(temp_path, self.sample_rate, audio_int16)

        self._debug_log(f"stop_recording: saved to {temp_path}")

        if self.on_recording_stop:
            self.on_recording_stop(temp_path)

        return temp_path

    def toggle_recording(self) -> Optional[str]:
        """Toggle recording state. Returns audio path when stopping."""
        with self._state_lock:
            currently_recording = self._recording

        if currently_recording:
            return self.stop_recording()
        else:
            self.start_recording()
            return None

    def get_audio_devices(self) -> list[dict]:
        """Get list of available audio input devices."""
        devices = sd.query_devices()
        input_devices = []

        for i, device in enumerate(devices):
            if device["max_input_channels"] > 0:
                input_devices.append({
                    "id": i,
                    "name": device["name"],
                    "channels": device["max_input_channels"],
                    "sample_rate": device["default_samplerate"],
                })

        return input_devices

    def set_device(self, device_id: Optional[int]) -> None:
        """Set the audio input device."""
        self.device = device_id

    def cleanup(self) -> None:
        """Clean up resources."""
        self._debug_log("cleanup called")
        with self._state_lock:
            if self._recording:
                self._recording = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
