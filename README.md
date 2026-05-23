# SayIt Local

**Voice typing that runs 100% locally on your Mac using OpenAI's Whisper.**

Hold `Ctrl + .` (period), speak, release - your words appear at the cursor. In any app.

## Features

- **100% Local** - All processing on your Mac, no cloud, no data leaves your device
- **Fast** - Uses `faster-whisper` with int8 optimization for Apple Silicon
- **Universal** - Works in any text field: browsers, editors, terminals, chat apps
- **Simple** - One hotkey, no setup wizard, just works
- **Private** - Only monitors `Ctrl + .`, nothing else

## Quick Start

Just run the install script:

```bash
cd voice_typing
./scripts/install.sh
```

That's it! The script will:
1. Create Python virtual environment
2. Install all dependencies
3. Verify packages
4. Check macOS permissions
5. Optionally enable auto-start at login

**Then grant permissions** (see below) and run `./scripts/start.sh`.

## Usage

Everything installs into `venv/` in this folder. **You do not need to activate venv** for normal use — `start.sh` calls `venv/bin/python3` directly.

```bash
# Start SayIt (uses venv automatically)
./scripts/start.sh

# Stop SayIt  
./scripts/stop.sh
```

Optional — manual run with venv activated:

```bash
source venv/bin/activate
python run.py
```

### Recording

1. Click into any text field
2. **Hold `Ctrl + .`** (Control + period)
3. Speak naturally
4. **Release** the keys
5. Text appears at your cursor!

## Each Folder Needs Its Own Install

**Important:** If you copy sayit to another location (Desktop, Downloads, USB), you must run install **in that folder**:

```bash
cd /path/to/that/copy/of/sayit
./scripts/install.sh
```

The `venv/` folder is **not portable** between copies. Permissions (Cursor.app) are system-wide and work everywhere, but packages only exist where you ran `install.sh`.

Verify any folder before use:

```bash
./venv/bin/python3 scripts/check_permissions.py
```

## Share with Others

Just share the entire `voice_typing` folder (zip without `venv/`). Recipients can:

```bash
# 1. Copy the folder anywhere
cp -r voice_typing ~/Desktop/

# 2. Run install
cd ~/Desktop/voice_typing
./scripts/install.sh

# 3. Grant permissions (see macOS Permissions section)
python3 ./scripts/check_permissions.py

# 4. Start using
./scripts/start.sh
```

## macOS Permissions (Required)

SayIt needs **two permissions** on the app you use to run it — **not** `sh`, `python3`, or the sayit folder.

### Which app to add?

| How you run SayIt | Add this in System Settings |
|-------------------|----------------------------|
| **Cursor** integrated terminal | **Cursor.app** |
| **VS Code** integrated terminal | **Visual Studio Code.app** |
| **Terminal.app** (macOS) | **Terminal.app** |
| **iTerm** | **iTerm.app** |

**Do not add** `/bin/sh`, `python3`, or `Python.app` — macOS will not accept them. **Cursor users: add only Cursor.app.**

If `./scripts/start.sh` says "Failed to start" but permissions look OK, check the log (`tail logs/sayit.log`) or run in foreground: `source venv/bin/activate && python run.py`

### Auto-detect your app

```bash
python3 ./scripts/check_permissions.py
```

This opens the right settings panes and prints the exact app path to add.

### Step-by-step (do for Accessibility AND Input Monitoring)

Use the **same app** in both places.

**1. Open System Settings**

- Apple menu → **System Settings** → **Privacy & Security**
- Open **Accessibility** first, then **Input Monitoring** second

**2. Unlock**

- Click the lock icon (bottom-left) and enter your Mac password

**3. Click the + button**

A file picker opens. You must select a real `.app` file.

**4. Find the app (after clicking +)**

1. Press **⌘ + Shift + G** (Go to Folder)
2. Paste the folder path:

| App | Paste this, then select |
|-----|-------------------------|
| **Cursor** | `/Applications` → **Cursor.app** |
| **Terminal** | `/System/Applications/Utilities` → **Terminal.app** |
| **iTerm** | `/Applications` → **iTerm.app** |
| **VS Code** | `/Applications` → **Visual Studio Code.app** |

3. Click **Open**

**5. Enable the toggle**

In the privacy list, turn **ON** the switch next to the app name.

**6. Repeat for the other permission**

| Setting | What it enables |
|---------|-----------------|
| **Accessibility** | Paste transcribed text at your cursor |
| **Input Monitoring** | Detect the `Ctrl + .` hotkey |

**7. Restart the host app (required)**

macOS only applies new permissions after a full quit:

1. **Quit** Cursor or Terminal with **⌘ + Q** (not just close the window)
2. Reopen the app
3. Run:

```bash
./scripts/start.sh
```

### Microphone (if recording fails)

**System Settings → Privacy & Security → Microphone** → enable the same app (**Cursor** or **Terminal**).

### Full guide

More detail and troubleshooting: [scripts/PERMISSIONS.md](scripts/PERMISSIONS.md)

## Auto-Start at Login

```bash
# Enable
./scripts/autostart.sh install

# Disable
./scripts/autostart.sh uninstall

# Check status
./scripts/autostart.sh status
```

## Configuration

Edit `~/.config/sayit/config.toml`:

```toml
[whisper]
model = "base"      # tiny, base, small, medium, large-v3
language = "en"     # or "auto" for detection

[hotkey]
hotkey = "ctrl+."   # Change if needed
mode = "push_to_talk"

[output]
use_clipboard = true
```

## Model Options

| Model | Speed | Accuracy | Download Size |
|-------|-------|----------|---------------|
| tiny | ~10x realtime | Basic | ~75MB |
| **base** | ~7x realtime | Good | ~150MB |
| small | ~4x realtime | Great | ~500MB |
| medium | ~2x realtime | Excellent | ~1.5GB |
| large-v3 | ~1x realtime | Best | ~3GB |

## Folder Structure

```
voice_typing/
├── scripts/
│   ├── install.sh            # One-command setup
│   ├── start.sh              # Start SayIt
│   ├── stop.sh               # Stop SayIt
│   ├── check_permissions.py  # Permission helper (run this first)
│   ├── PERMISSIONS.md        # Detailed permission guide
│   └── autostart.sh          # Auto-start at login
├── src/                      # Core Python code
├── config/                   # Default configuration
├── run.py                    # Entry point
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## Troubleshooting

### "I can't add /bin/sh" or checker says Running from: /bin/sh

**Correct** — never add `sh`. Add **Cursor.app** or **Terminal.app** instead (see [macOS Permissions](#macos-permissions-required)).

### "This process is not trusted"

1. Grant **Input Monitoring** and **Accessibility** to **Cursor.app** or **Terminal.app**
2. Quit the app fully (**⌘ + Q**), reopen, run `./scripts/start.sh` again

### Hotkey not working (`Ctrl + .` does nothing)

1. Run `python3 ./scripts/check_permissions.py`
2. Confirm **Input Monitoring** is ON for your terminal app
3. Quit and reopen Cursor/Terminal
4. Ensure no other app uses `Ctrl + .`

### Text not inserting at cursor

1. Confirm **Accessibility** is ON for the same app
2. Click in a text field **before** you release the hotkey
3. Run checker again after restart

### Running from Downloads or any folder

The folder path does not matter. Permissions always go to **Cursor**, **Terminal**, or **iTerm** — whichever app runs the terminal command.

### Wrong language detected

Set `language = "en"` in `~/.config/sayit/config.toml` (or your language code).

## Privacy

- All audio processed locally using faster-whisper
- No network calls, no telemetry, no analytics
- Audio is deleted immediately after transcription
- Only `Ctrl + .` hotkey is monitored, nothing else logged

## Requirements

- macOS 13.0+ (Ventura or later)
- Python 3.9+
- ~500MB disk space (with base model)
- ~2GB RAM while running

## License

MIT
