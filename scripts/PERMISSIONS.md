# SayIt — macOS Permissions Guide

SayIt needs **two permissions** for the app you use to run it (not `sh` or `python3`).

## Which app to add?

| How you run SayIt | Add this in System Settings |
|-------------------|----------------------------|
| **Cursor** terminal (most common) | **Cursor.app** |
| **VS Code** terminal | **Visual Studio Code.app** |
| **Terminal.app** (macOS) | **Terminal.app** |
| **iTerm** | **iTerm.app** |

Run the checker — it tells you which app was detected:

```bash
python3 scripts/check_permissions.py
```

---

## Step-by-step (Accessibility & Input Monitoring)

Do this **twice** — once for **Accessibility**, once for **Input Monitoring**.

### 1. Open System Settings

- Apple menu → **System Settings**
- **Privacy & Security**
- **Accessibility** (first) or **Input Monitoring** (second)

### 2. Unlock (if needed)

- Click the **lock** bottom-left
- Enter your Mac password

### 3. Click the **+** button

A file picker opens. You **cannot** type `sh` or `python3` here — you must pick a real **.app** bundle.

### 4. Go to the app folder

1. In the file picker, press **⌘ + Shift + G** (Go to Folder)
2. Paste one of these paths:

| App | Paste this path |
|-----|-----------------|
| **Cursor** | `/Applications` then select **Cursor.app** |
| **Terminal** | `/System/Applications/Utilities` then **Terminal.app** |
| **iTerm** | `/Applications` then **iTerm.app** |
| **VS Code** | `/Applications` then **Visual Studio Code.app** |

3. Click **Open**

### 5. Enable the toggle

Back in the privacy list, turn **ON** the switch next to the app name.

### 6. Repeat for the other permission

- **Accessibility** — paste text at cursor
- **Input Monitoring** — detect Ctrl+. hotkey

Use the **same app** for both.

### 7. Restart the host app

**Important:** macOS only applies permissions after restart.

1. **Quit** Cursor or Terminal completely (**⌘ + Q**, not just close the window)
2. Reopen it
3. Start SayIt: `./scripts/start.sh`

---

## Microphone (optional check)

If recording fails:

- **System Settings → Privacy & Security → Microphone**
- Enable **Cursor** or **Terminal** (same app as above)

---

## Troubleshooting

### "I can't add /bin/sh"

Correct — **never add sh**. Add **Cursor.app** or **Terminal.app** instead.

### Running from Downloads folder

Path doesn't matter. Permissions go to **Cursor** or **Terminal**, not the sayit folder.

### Permissions on but hotkey still fails

1. Quit host app (⌘Q)
2. Reopen
3. `./scripts/stop.sh` then `./scripts/start.sh`
4. Run checker again: `python3 scripts/check_permissions.py`

### Using Cursor specifically

1. Open SayIt project in Cursor
2. Open integrated terminal (`` Ctrl + ` ``)
3. Run `./scripts/install.sh` and `./scripts/start.sh` from that terminal
4. Grant permissions to **Cursor.app** in both Accessibility and Input Monitoring
