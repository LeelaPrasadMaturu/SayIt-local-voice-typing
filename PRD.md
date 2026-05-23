# SayIt Local - Product Requirements Document

## Overview

**SayIt Local** is a native macOS voice typing application that runs entirely on-device using OpenAI's Whisper model. It provides real-time speech-to-text transcription with system-wide text insertion capabilities, optimized for Apple Silicon Macs.

---

## Problem Statement

Current voice typing solutions either:
- Require constant internet connectivity and send audio to cloud servers (privacy concerns)
- Have noticeable latency due to network round-trips
- Lack system-wide integration (only work in specific apps)
- Require subscription fees for quality transcription

**SayIt Local** solves these by running Whisper locally with zero latency, complete privacy, and universal text insertion.

---

## Goals

1. **Zero-latency transcription** - Real-time voice-to-text with minimal delay
2. **Complete privacy** - All processing happens on-device, no data leaves the system
3. **System-wide integration** - Works in any text field across all applications
4. **Always available** - Global hotkey activation from anywhere
5. **High accuracy** - Leverage Whisper's state-of-the-art accuracy

---

## Target User

- macOS users with Apple Silicon (M1/M2/M3/M4) or Intel Macs with dedicated GPU
- Power users who value privacy and speed
- Developers, writers, and professionals who frequently type long-form content
- Users who want voice typing without subscription costs

---

## System Requirements

### Minimum
- macOS 13.0 (Ventura) or later
- Apple Silicon (M1) or Intel Mac with 16GB RAM
- 5GB free disk space (for Whisper models)

### Recommended (Your System)
- Apple Silicon M2/M3/M4 Pro/Max
- 32GB+ RAM
- 10GB free disk space (for larger models)

---

## Core Features

### 1. Voice Recording & Activation

| Feature | Description | Priority |
|---------|-------------|----------|
| Global hotkey | Configurable system-wide shortcut (default: `⌥ + Space`) | P0 |
| Push-to-talk | Hold hotkey to record, release to transcribe | P0 |
| Toggle mode | Press once to start, press again to stop | P1 |
| Auto-detect silence | Automatically stop recording after silence threshold | P1 |
| Audio input selection | Choose microphone source | P1 |
| Visual feedback | Menu bar indicator showing recording state | P0 |

### 2. Transcription Engine

| Feature | Description | Priority |
|---------|-------------|----------|
| Whisper model support | Support for tiny, base, small, medium, large-v3 models | P0 |
| Model selection | User can choose model based on speed/accuracy preference | P0 |
| Language detection | Auto-detect spoken language | P1 |
| Language forcing | Option to specify expected language | P1 |
| Punctuation | Automatic punctuation and capitalization | P0 |
| GPU acceleration | Metal/CoreML optimization for Apple Silicon | P0 |

### 3. Text Output & Cursor Insertion

The core functionality is inserting transcribed text **at the blinking cursor (caret)** in any active text field system-wide.

| Feature | Description | Priority |
|---------|-------------|----------|
| Cursor insertion | Insert text exactly where the blinking caret is positioned | P0 |
| Universal compatibility | Works in any app: browsers, editors, terminals, native apps | P0 |
| Clipboard fallback | Copy to clipboard if direct insertion fails | P1 |
| Text formatting | Options for case formatting (lowercase, UPPERCASE, Title Case) | P2 |
| Custom replacements | User-defined text replacements (e.g., "period" → ".") | P2 |

#### How Cursor Insertion Works (Technical)

There are **two methods** to insert text at the cursor position on macOS:

**Method 1: Keyboard Simulation (Recommended)**
```
User speaks → Whisper transcribes → pynput types each character → Text appears at cursor
```
- Uses `pynput.keyboard.Controller().type("transcribed text")`
- Simulates actual keystrokes, character by character
- Works in ANY text field where you can type
- Requires **Accessibility permission** in macOS

**Method 2: Clipboard Paste (Fallback)**
```
User speaks → Whisper transcribes → Copy to clipboard → Simulate ⌘V → Text appears at cursor
```
- Copies text to clipboard via `pyperclip`
- Simulates ⌘+V keystroke
- Faster for long text, but overwrites clipboard
- Also requires **Accessibility permission**

#### Why It Works Anywhere

The blinking cursor (caret) indicates the active text insertion point in the **focused application**. When we simulate keystrokes:
1. macOS routes keystrokes to the **frontmost/focused application**
2. That app's text field receives the input at its **current cursor position**
3. Text appears exactly where the user was about to type

This is the same mechanism the macOS built-in dictation uses.

### 4. User Interface

| Feature | Description | Priority |
|---------|-------------|----------|
| Menu bar app | Lightweight menu bar presence | P0 |
| Recording indicator | Visual/audio feedback during recording | P0 |
| Settings panel | Native macOS preferences window | P0 |
| Transcription history | View recent transcriptions | P2 |
| Usage statistics | Track transcription time and word count | P3 |

---

## Technical Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     SayIt Local                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  System     │  │   Hotkey    │  │    Settings         │  │
│  │  Tray/Menu  │  │   Manager   │  │     GUI             │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┼─────────────────────┘             │
│                          │                                   │
│                    ┌─────▼─────┐                             │
│                    │   Core    │                             │
│                    │  Engine   │                             │
│                    └─────┬─────┘                             │
│         ┌────────────────┼────────────────┐                  │
│         │                │                │                  │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐          │
│  │    Audio    │  │   Whisper   │  │    Text     │          │
│  │   Capture   │  │   Engine    │  │  Insertion  │          │
│  │ (sounddevice│  │  (openai-   │  │ (pyautogui/ │          │
│  │  /pyaudio)  │  │   whisper)  │  │  pynput)    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Options

### **Option A: Python (Recommended)**

Python is the ideal choice because OpenAI's Whisper has first-class Python support with excellent GPU acceleration.

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Language | Python 3.10+ | Native Whisper support, rapid development |
| Whisper Engine | openai-whisper / faster-whisper | Official implementation with CUDA/MPS support |
| Audio Capture | sounddevice + numpy | Low-latency audio capture, cross-platform |
| Text Insertion | pynput / pyautogui | System-wide keyboard simulation |
| Global Hotkey | pynput | Cross-platform hotkey listener |
| System Tray | pystray + Pillow | Menu bar/system tray icon |
| GUI (Settings) | rumps (macOS) or PyQt6 | Native settings window |
| GPU Acceleration | torch with MPS (Apple Silicon) | Native Metal acceleration via PyTorch |
| Storage | JSON / TOML config files | Simple, human-readable settings |

**Python Advantages:**
- Official Whisper library with best accuracy
- `faster-whisper` provides 4x speedup with same accuracy
- Native Apple Silicon GPU support via PyTorch MPS backend
- Rapid prototyping and iteration
- Large ecosystem for audio processing

### **Option B: JavaScript/TypeScript (Electron)**

For a more polished desktop app with a modern UI.

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Language | TypeScript | Type safety, modern tooling |
| Framework | Electron | Cross-platform desktop app |
| Whisper Engine | whisper.cpp (via node bindings) or whisper-node | Fast C++ implementation |
| Audio Capture | Web Audio API / node-audiorecorder | Browser-native audio |
| Text Insertion | robotjs / nut.js | System-wide keyboard simulation |
| Global Hotkey | electron globalShortcut | Built-in Electron API |
| UI | React + Tailwind | Modern, responsive UI |
| Storage | electron-store | Persistent settings |

**JavaScript Advantages:**
- Beautiful UI with web technologies
- Single codebase for all platforms
- Easier to build complex settings panels
- Hot reload during development

### **Option C: Hybrid (Python Backend + Electron Frontend)**

Best of both worlds for complex applications.

| Component | Technology |
|-----------|------------|
| Backend | Python (FastAPI) running as local service |
| Whisper | openai-whisper / faster-whisper |
| Frontend | Electron + React |
| Communication | WebSocket / HTTP localhost |

---

## Recommended Approach: Python

For your powerful Mac system, **Python with faster-whisper** is the recommended approach:

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Language | Python 3.11+ | Best Whisper ecosystem |
| Whisper | faster-whisper | 4x faster than original, same accuracy |
| Audio | sounddevice | Low-latency, reliable |
| Hotkey | pynput | Works system-wide on macOS |
| Text Insertion | pynput | Simulates keyboard input anywhere |
| System Tray | rumps | Native macOS menu bar app |
| GPU | PyTorch MPS | Apple Silicon acceleration |
| Config | TOML | Human-readable settings |

### Whisper Model Options

| Model | Size | VRAM | Speed | Accuracy | Recommended For |
|-------|------|------|-------|----------|-----------------|
| tiny | 75MB | ~1GB | Fastest | Good | Quick notes |
| base | 142MB | ~1GB | Very Fast | Better | General use |
| small | 466MB | ~2GB | Fast | Great | **Default choice** |
| medium | 1.5GB | ~5GB | Moderate | Excellent | Long-form content |
| large-v3 | 3GB | ~10GB | Slower | Best | Maximum accuracy |

---

## User Flows

### Primary Flow: Voice Typing

```
1. User clicks into any text field (browser, editor, Slack, Notes, etc.)
   → Blinking cursor (caret) appears indicating insertion point
   
2. User presses global hotkey (⌥ + Space)
   → Hotkey works even though another app is focused
   → Menu bar icon changes to recording state (red dot)
   
3. User speaks naturally
   → Audio is captured in the background
   → User can see the text field and cursor the whole time
   
4. User releases hotkey (or presses again in toggle mode)
   → Recording stops
   → Brief processing indicator shows
   
5. Whisper transcribes the audio
   → Runs locally on GPU for speed
   
6. Text is "typed" at the cursor position
   → pynput simulates keystrokes
   → Characters appear one-by-one (very fast) at the blinking cursor
   → Works exactly like typing, but automatic
   
7. Menu bar icon returns to idle state
   → User can continue typing or dictate again
```

### Example Scenarios

| App | Text Field | Result |
|-----|-----------|--------|
| Chrome | Google Docs, Gmail compose, search bar | Text appears at cursor |
| VS Code | Code editor, search box, terminal | Text appears at cursor |
| Slack | Message input | Text appears at cursor |
| Notes | Note body | Text appears at cursor |
| Terminal | Command line | Text appears at cursor |
| Any app | Any text input | Text appears at cursor |

### Settings Flow

```
1. User clicks menu bar icon
2. User selects "Preferences..."
3. Settings window opens with tabs:
   - General (hotkey, mode, startup)
   - Transcription (model, language, punctuation)
   - Audio (input device, silence detection)
   - Advanced (GPU settings, cache)
```

---

## Permissions Required

| Permission | Purpose | When Requested |
|------------|---------|----------------|
| Microphone | Audio capture for transcription | First recording attempt |
| Accessibility | Text insertion and global hotkey | First launch |
| Input Monitoring | Global hotkey detection | First launch |

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Recording start latency | < 50ms | From hotkey press to recording |
| Transcription latency (small model) | < 0.5x real-time | 10s audio → <5s processing |
| Transcription latency (large model) | < 1x real-time | 10s audio → <10s processing |
| Memory usage (idle) | < 100MB | Menu bar app only |
| Memory usage (active) | < 2GB | During transcription (model dependent) |
| CPU usage (idle) | < 1% | Background state |

---

## Development Phases

### Phase 1: MVP (Core Functionality)
- [ ] Project setup with virtual environment
- [ ] Global hotkey registration (⌥ + Space) using pynput
- [ ] Audio recording with sounddevice
- [ ] faster-whisper integration with small model
- [ ] Basic text insertion via pynput keyboard controller
- [ ] Simple terminal/console indicator for recording state
- [ ] Basic config file (TOML) for settings

### Phase 2: System Tray & Polish
- [ ] Menu bar app using rumps (macOS)
- [ ] Recording state indicator in menu bar
- [ ] Settings GUI window
- [ ] Model download manager with progress
- [ ] Multiple model support (tiny → large)
- [ ] Audio input device selection
- [ ] Push-to-talk vs toggle mode

### Phase 3: Performance & UX
- [ ] GPU acceleration with PyTorch MPS
- [ ] Silence detection for auto-stop (VAD)
- [ ] Visual/audio feedback (sound on start/stop)
- [ ] Language detection and selection
- [ ] Custom text replacements
- [ ] Clipboard mode option

### Phase 4: Advanced Features
- [ ] Transcription history with search
- [ ] Usage statistics dashboard
- [ ] Voice commands ("new paragraph", "delete that")
- [ ] Custom vocabulary/names
- [ ] Auto-start on login
- [ ] Export transcription history

---

## File Structure

### Python Implementation

```
whisper_flow/
├── src/
│   ├── __init__.py
│   ├── main.py                    # App entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── audio_recorder.py      # sounddevice recording
│   │   ├── whisper_engine.py      # faster-whisper wrapper
│   │   ├── text_inserter.py       # pynput keyboard simulation
│   │   └── hotkey_manager.py      # Global hotkey handling
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── menu_bar.py            # rumps menu bar app (macOS)
│   │   └── settings_window.py     # Settings GUI
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # TOML config management
│       ├── model_manager.py       # Model download/selection
│       └── audio_utils.py         # Audio processing helpers
├── config/
│   └── settings.toml              # User configuration
├── models/                        # Downloaded Whisper models (gitignored)
├── assets/
│   ├── icon.png                   # Menu bar icon
│   └── icon_recording.png         # Recording state icon
├── tests/
│   ├── test_audio.py
│   ├── test_whisper.py
│   └── test_hotkey.py
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project metadata
├── README.md
└── run.py                         # Quick start script
```

### JavaScript/Electron Implementation (Alternative)

```
whisper_flow/
├── src/
│   ├── main/
│   │   ├── index.ts               # Electron main process
│   │   ├── hotkey.ts              # Global shortcut handling
│   │   ├── tray.ts                # System tray management
│   │   └── whisper.ts             # whisper.cpp bindings
│   ├── renderer/
│   │   ├── App.tsx                # React app root
│   │   ├── components/
│   │   │   ├── Settings.tsx       # Settings panel
│   │   │   └── RecordingStatus.tsx
│   │   └── hooks/
│   │       └── useRecording.ts    # Recording state hook
│   └── preload/
│       └── index.ts               # Electron preload script
├── native/                        # Native Node addons
│   └── whisper-binding/           # whisper.cpp Node bindings
├── assets/
│   └── icons/
├── package.json
├── tsconfig.json
├── electron-builder.json
└── README.md
```

---

## Dependencies

### Python Dependencies (requirements.txt)

```txt
# Core
faster-whisper>=1.0.0          # Optimized Whisper implementation (4x faster)
torch>=2.0.0                   # PyTorch for GPU acceleration (MPS on Mac)
numpy>=1.24.0                  # Audio array processing

# Audio
sounddevice>=0.4.6             # Audio recording
scipy>=1.11.0                  # Audio file I/O

# System Integration
pynput>=1.7.6                  # Global hotkey + text insertion
pyperclip>=1.8.2               # Clipboard operations

# macOS Menu Bar
rumps>=0.4.0                   # macOS menu bar app framework
Pillow>=10.0.0                 # Icon handling

# Configuration
toml>=0.10.2                   # Config file parsing

# Optional: Better VAD (Voice Activity Detection)
webrtcvad>=2.0.10              # Voice activity detection
silero-vad>=4.0                # Alternative neural VAD
```

### JavaScript/Electron Dependencies (package.json)

```json
{
  "dependencies": {
    "whisper-node": "^1.0.0",
    "robotjs": "^0.6.0",
    "electron-store": "^8.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "electron": "^28.0.0",
    "electron-builder": "^24.0.0",
    "typescript": "^5.3.0",
    "@types/node": "^20.0.0",
    "tailwindcss": "^3.4.0"
  }
}
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Transcription accuracy (English) | > 95% word accuracy |
| Time from speech end to text insertion | < 2 seconds (small model) |
| App crash rate | < 0.1% of sessions |
| Memory leak | Zero after extended use |
| User satisfaction | Replaces cloud-based alternatives |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large model download size | Poor first-run experience | Progressive download, start with small model |
| Accessibility permission denied | App non-functional | Clear onboarding, permission guidance |
| GPU memory exhaustion | Transcription fails | Graceful fallback to smaller model or CPU |
| Microphone quality variance | Poor accuracy | Audio preprocessing, gain normalization |
| macOS permission prompts | Confusing UX | Guide user through permissions in README |
| pynput compatibility | May break on macOS updates | Monitor releases, have fallback to pyautogui |
| Python packaging complexity | Hard to distribute | Use PyInstaller or py2app for standalone app |

---

## Open Questions

1. **Model bundling vs download**: Should we bundle a default model or download on first use?
   - *Recommendation*: Download on first use to reduce app size

2. **Streaming vs batch transcription**: Process audio in real-time or after recording?
   - *Recommendation*: Start with batch (simpler), add streaming later

3. **Python vs Electron**: Which stack to use?
   - *Recommendation*: **Python** for your use case - simpler, faster Whisper integration, better GPU support

4. **faster-whisper vs openai-whisper**: Which Whisper implementation?
   - *Recommendation*: `faster-whisper` - 4x faster with same accuracy, lower memory usage

5. **Distribution method**: How to package for easy installation?
   - *Recommendation*: Start with `pip install`, later create standalone app with PyInstaller

---

## References

### Python Stack
- [OpenAI Whisper](https://github.com/openai/whisper) - Original Whisper implementation
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - CTranslate2-based, 4x faster
- [sounddevice](https://python-sounddevice.readthedocs.io/) - Audio recording library
- [pynput](https://pynput.readthedocs.io/) - Keyboard/mouse control and monitoring
- [rumps](https://github.com/jaredks/rumps) - macOS menu bar apps in Python

### JavaScript Stack
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) - C++ Whisper implementation
- [Electron](https://www.electronjs.org/) - Desktop app framework
- [robotjs](https://robotjs.io/) - Node.js desktop automation

### macOS Permissions
- [Input Monitoring Permission](https://developer.apple.com/documentation/security/app_sandbox/protecting_user_data_with_app_sandbox) - Required for global hotkeys
- [Accessibility Permission](https://developer.apple.com/documentation/accessibility) - Required for text insertion

---

## Appendix: Comparison with Alternatives

| Feature | SayIt Local | macOS Dictation | Whisper Transcription (Cloud) |
|---------|-------------------|-----------------|------------------------------|
| Privacy | ✅ Fully local | ⚠️ Apple servers | ❌ Third-party servers |
| Latency | ✅ <2s | ✅ Real-time | ⚠️ Network dependent |
| Accuracy | ✅ Excellent | ⚠️ Good | ✅ Excellent |
| Cost | ✅ Free | ✅ Free | ❌ Per-minute pricing |
| Offline | ✅ Yes | ⚠️ Partial | ❌ No |
| Customization | ✅ Full | ❌ Limited | ⚠️ API only |

---

---

## Appendix: Quick Start Commands (Python)

### Initial Setup

```bash
# Create project directory
cd ~/Desktop/voice_typing

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install core dependencies
pip install faster-whisper sounddevice pynput rumps numpy scipy toml pillow

# For Apple Silicon GPU acceleration
pip install torch torchvision torchaudio

# Download a Whisper model (first run)
# faster-whisper auto-downloads models, or manually:
# python -c "from faster_whisper import WhisperModel; WhisperModel('small')"
```

### Grant macOS Permissions

1. **Microphone**: System Settings → Privacy & Security → Microphone → Enable for Terminal/Python
2. **Accessibility**: System Settings → Privacy & Security → Accessibility → Add Terminal/Python
3. **Input Monitoring**: System Settings → Privacy & Security → Input Monitoring → Add Terminal/Python

### Minimal Working Example

```python
# test_whisper.py - Quick test to verify setup
from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write

# Record 5 seconds of audio
print("Recording for 5 seconds...")
fs = 16000
duration = 5
audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
sd.wait()
print("Recording complete!")

# Save temporarily
write('/tmp/test_audio.wav', fs, audio)

# Transcribe
print("Transcribing...")
model = WhisperModel("small", device="cpu", compute_type="int8")  # Use "cuda" or "mps" for GPU
segments, info = model.transcribe('/tmp/test_audio.wav')

print(f"Detected language: {info.language}")
for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
```

### Text Insertion at Cursor - Demo

This demonstrates inserting text at the blinking cursor in ANY app:

```python
# test_cursor_insert.py - Test typing at cursor position
# 
# HOW TO TEST:
# 1. Run this script
# 2. You have 3 seconds to click into any text field (browser, Notes, etc.)
# 3. Watch the text appear at your cursor!

import time
from pynput.keyboard import Controller, Key

keyboard = Controller()

print("You have 3 seconds to click into a text field...")
print("Click where you want text to appear (where the blinking cursor is)")
time.sleep(3)

# Method 1: Type character by character (works everywhere)
text = "Hello! This text was inserted at your cursor position. 🎤"
print(f"Typing: {text}")
keyboard.type(text)

print("\nDone! The text should appear where your cursor was blinking.")
```

### Full Voice-to-Cursor Demo

```python
# voice_to_cursor.py - Complete demo: speak → text appears at cursor
#
# 1. Run this script  
# 2. Click into any text field (you have 2 seconds)
# 3. Speak for up to 5 seconds
# 4. Watch your words appear at the cursor!

import time
import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
from pynput.keyboard import Controller

def record_audio(duration=5, sample_rate=16000):
    """Record audio from microphone"""
    print(f"🎤 Recording for {duration} seconds... Speak now!")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    print("✓ Recording complete")
    return audio, sample_rate

def transcribe(audio, sample_rate, model):
    """Transcribe audio using Whisper"""
    # Save to temp file (faster-whisper needs a file)
    write('/tmp/voice_input.wav', sample_rate, audio)
    
    print("🔄 Transcribing...")
    segments, info = model.transcribe('/tmp/voice_input.wav')
    text = " ".join([seg.text for seg in segments]).strip()
    print(f"✓ Transcribed: {text}")
    return text

def type_at_cursor(text):
    """Type text at the current cursor position"""
    keyboard = Controller()
    print("⌨️  Typing at cursor...")
    keyboard.type(text)
    print("✓ Done!")

# Main flow
print("Loading Whisper model (first run downloads ~500MB)...")
model = WhisperModel("small", device="cpu", compute_type="int8")

print("\n" + "="*50)
print("Click into a text field NOW! You have 2 seconds...")
print("="*50)
time.sleep(2)

audio, sr = record_audio(duration=5)
text = transcribe(audio, sr, model)

if text:
    type_at_cursor(text)
else:
    print("No speech detected")
```

---

*Document Version: 1.1*  
*Created: May 19, 2026*  
*Updated: May 19, 2026 - Added Python/JS stack options*  
*Author: SayIt Team*
