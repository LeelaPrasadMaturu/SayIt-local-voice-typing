"""Whisper transcription engine using faster-whisper (CPU, Apple Silicon optimized)."""

import os
import wave
import concurrent.futures
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    """Result of a transcription."""
    text: str
    language: str
    duration: float
    segments: list[dict]


class WhisperEngine:
    """Local speech-to-text using faster-whisper (CTranslate2).

    Uses int8 on CPU — fast on Apple Silicon M-series chips.
    """

    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large-v3"]
    DEFAULT_MODEL = "base"

    # Prevents infinite hang if VAD/model stalls
    TRANSCRIBE_TIMEOUT_SEC = 120

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str = "auto",
        compute_type: str = "auto",
        language: Optional[str] = None,
    ):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self._model = None
        self._cpu_threads = self._detect_cpu_threads()

    def _detect_cpu_threads(self) -> int:
        try:
            cpu_count = os.cpu_count() or 4
            return max(4, cpu_count // 2)
        except Exception:
            return 4

    def _get_device_and_compute(self) -> tuple[str, str]:
        device = self.device
        compute_type = self.compute_type

        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        if compute_type == "auto":
            compute_type = "float16" if device == "cuda" else "int8"

        return device, compute_type

    def _get_audio_duration(self, audio_path: str) -> float:
        try:
            with wave.open(audio_path, "rb") as wf:
                return wf.getnframes() / float(wf.getframerate())
        except Exception:
            return 0.0

    def load_model(self) -> None:
        if self._model is not None:
            return

        from faster_whisper import WhisperModel

        device, compute_type = self._get_device_and_compute()

        print(
            f"Loading faster-whisper '{self.model_name}' "
            f"on {device} ({compute_type}, {self._cpu_threads} threads)...",
            flush=True,
        )

        self._model = WhisperModel(
            self.model_name,
            device=device,
            compute_type=compute_type,
            cpu_threads=self._cpu_threads,
        )

        print("faster-whisper model loaded.", flush=True)

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """Transcribe with a hard timeout so the UI never hangs forever."""
        if self._model is None:
            self.load_model()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self._transcribe_impl, audio_path)
            try:
                return future.result(timeout=self.TRANSCRIBE_TIMEOUT_SEC)
            except concurrent.futures.TimeoutError:
                raise RuntimeError(
                    f"Transcription timed out after {self.TRANSCRIBE_TIMEOUT_SEC}s. "
                    "Try a shorter clip or set model = 'tiny' in ~/.config/sayit/config.toml"
                )

    def _transcribe_impl(self, audio_path: str) -> TranscriptionResult:
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        audio_duration = self._get_audio_duration(audio_path)
        print(f"  Audio: {audio_duration:.1f}s — transcribing...", flush=True)

        if audio_duration < 0.3:
            print("  Audio too short, skipping.", flush=True)
            return TranscriptionResult(
                text="",
                language=self.language or "en",
                duration=audio_duration,
                segments=[],
            )

        # Root cause of "infinite" hang: vad_filter=True on short push-to-talk clips.
        # Silero VAD can stall or run very long on 2–20s recordings.
        use_vad = audio_duration > 30.0

        kwargs = dict(
            language=self.language,
            beam_size=1,
            best_of=1,
            patience=1,
            vad_filter=use_vad,
            condition_on_previous_text=False,
            temperature=0.0,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6,
        )
        if use_vad:
            kwargs["vad_parameters"] = dict(
                min_silence_duration_ms=500,
                speech_pad_ms=100,
            )

        segments_gen, info = self._model.transcribe(audio_path, **kwargs)

        segments = []
        text_parts = []

        for segment in segments_gen:
            segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
            })
            text_parts.append(segment.text.strip())

        full_text = " ".join(text_parts).strip()

        print(
            f"  Done: {len(segments)} segment(s), {len(full_text)} chars",
            flush=True,
        )

        return TranscriptionResult(
            text=full_text,
            language=info.language or self.language or "en",
            duration=info.duration if info.duration else audio_duration,
            segments=segments,
        )

    def change_model(self, model_name: str) -> None:
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Unknown model: {model_name}. Available: {self.AVAILABLE_MODELS}"
            )
        self._model = None
        self.model_name = model_name

    def set_language(self, language: Optional[str]) -> None:
        self.language = language

    def unload_model(self) -> None:
        self._model = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def backend(self) -> str:
        return "faster-whisper"

    @property
    def backend_info(self) -> str:
        if self._model is None:
            return "faster-whisper (not loaded)"
        device, compute_type = self._get_device_and_compute()
        return f"faster-whisper ({device}, {compute_type})"

    @classmethod
    def get_recommended_model(cls) -> str:
        return cls.DEFAULT_MODEL
