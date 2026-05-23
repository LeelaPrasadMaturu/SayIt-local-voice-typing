"""Configuration management using TOML."""

import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
import toml


@dataclass
class AudioConfig:
    """Audio recording configuration."""
    sample_rate: int = 16000
    channels: int = 1
    device_id: Optional[int] = None


@dataclass
class WhisperConfig:
    """Whisper transcription configuration (faster-whisper only)."""
    model: str = "base"  # tiny, base, small, medium, large-v3
    device: str = "auto"
    compute_type: str = "auto"
    language: Optional[str] = "en"  # Force English to avoid misdetection


@dataclass
class HotkeyConfig:
    """Hotkey configuration."""
    hotkey: str = "ctrl+."  # Ctrl + period
    mode: str = "push_to_talk"


@dataclass
class OutputConfig:
    """Text output configuration."""
    use_clipboard: bool = True
    typing_delay: float = 0.0
    add_trailing_space: bool = True


@dataclass
class AppConfig:
    """Application configuration."""
    start_on_login: bool = False
    show_notifications: bool = True
    play_sounds: bool = True


@dataclass
class Config:
    """Main configuration container."""
    audio: AudioConfig = field(default_factory=AudioConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    hotkey: HotkeyConfig = field(default_factory=HotkeyConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    app: AppConfig = field(default_factory=AppConfig)

    @classmethod
    def get_config_path(cls) -> Path:
        """Get the configuration file path."""
        config_dir = Path.home() / ".config" / "sayit"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.toml"

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        """Load configuration from file.
        
        Args:
            path: Path to config file, or None for default location
            
        Returns:
            Config instance
        """
        config_path = path or cls.get_config_path()
        
        if not config_path.exists():
            config = cls()
            config.save(config_path)
            return config

        try:
            data = toml.load(config_path)

            # Drop removed keys from older configs (e.g. backend = "mlx")
            whisper_data = data.get("whisper", {})
            whisper_fields = {f.name for f in WhisperConfig.__dataclass_fields__.values()}
            whisper_data = {k: v for k, v in whisper_data.items() if k in whisper_fields}
            
            config = cls(
                audio=AudioConfig(**data.get("audio", {})),
                whisper=WhisperConfig(**whisper_data),
                hotkey=HotkeyConfig(**data.get("hotkey", {})),
                output=OutputConfig(**data.get("output", {})),
                app=AppConfig(**data.get("app", {})),
            )
            # Auto-migrate old defaults that conflict with Raycast or app shortcuts.
            if config.hotkey.hotkey in (
                "alt+space",
                "option+space",
                "option+x",
                "ctrl+x",
                "control+x",
                "f9",
                "ctrl+shift+d",
            ):
                config.hotkey.hotkey = "ctrl+."
                config.save(config_path)
            if not config.output.use_clipboard:
                config.output.use_clipboard = True
                config.save(config_path)
            # Force English to avoid misdetection (Hindi gibberish issue)
            if config.whisper.language is None:
                config.whisper.language = "en"
                config.save(config_path)
            return config
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
            return cls()

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to file.
        
        Args:
            path: Path to config file, or None for default location
        """
        config_path = path or self.get_config_path()
        
        data = {
            "audio": asdict(self.audio),
            "whisper": asdict(self.whisper),
            "hotkey": asdict(self.hotkey),
            "output": asdict(self.output),
            "app": asdict(self.app),
        }

        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w") as f:
            toml.dump(data, f)

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "audio": asdict(self.audio),
            "whisper": asdict(self.whisper),
            "hotkey": asdict(self.hotkey),
            "output": asdict(self.output),
            "app": asdict(self.app),
        }


def get_default_config_content() -> str:
    """Get default configuration file content as string."""
    return '''# SayIt Configuration

[audio]
sample_rate = 16000
channels = 1
# device_id = 0  # Uncomment and set to specific device ID

[whisper]
# Engine: faster-whisper (CPU, int8 on Apple Silicon)
# Models: tiny (fastest), base, small, medium, large-v3
model = "base"
device = "auto"
compute_type = "auto"
language = "en"

[hotkey]
hotkey = "ctrl+."  # Hold Ctrl+. while speaking, release to transcribe.
mode = "push_to_talk"  # push_to_talk or toggle

[output]
use_clipboard = true  # Always pastes full text at once
typing_delay = 0.0  # Unused (clipboard paste only)
add_trailing_space = true  # Add space after transcribed text

[app]
start_on_login = false
show_notifications = true
play_sounds = true
'''
