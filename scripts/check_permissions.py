#!/usr/bin/env python3
"""
SayIt Permission Checker
Checks and helps grant macOS Accessibility and Input Monitoring permissions.
"""

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class HostApp:
    """The macOS application that must receive permissions."""
    name: str           # e.g. "Cursor.app"
    path: str           # e.g. "/Applications/Cursor.app"
    how_launched: str   # e.g. "Cursor integrated terminal"


# GUI host apps only — never suggest Python/sh (order = priority)
KNOWN_APPS = [
    ("Cursor", "Cursor.app", [
        "/Applications/Cursor.app",
        os.path.expanduser("~/Applications/Cursor.app"),
    ]),
    ("Code", "Visual Studio Code.app", [
        "/Applications/Visual Studio Code.app",
    ]),
    ("iTerm2", "iTerm.app", [
        "/Applications/iTerm.app",
        os.path.expanduser("~/Applications/iTerm.app"),
    ]),
    ("iTerm", "iTerm.app", [
        "/Applications/iTerm.app",
    ]),
    ("Warp", "Warp.app", [
        "/Applications/Warp.app",
    ]),
    ("Terminal", "Terminal.app", [
        "/System/Applications/Utilities/Terminal.app",
        "/Applications/Utilities/Terminal.app",
    ]),
]

SHELL_NAMES = {"sh", "bash", "zsh", "fish", "dash", "ksh", "csh"}
SKIP_NAMES = SHELL_NAMES | {"python", "python3", "python3.9", "python3.10", "python3.11", "python3.12"}


def _first_existing_path(paths: list[str]) -> Optional[str]:
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


def _get_ppid(pid: int) -> int:
    try:
        r = subprocess.run(
            ["ps", "-p", str(pid), "-o", "ppid="],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return int(r.stdout.strip())
    except Exception:
        return 0


def _get_process_name(pid: int) -> str:
    try:
        r = subprocess.run(
            ["ps", "-p", str(pid), "-o", "comm="],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return r.stdout.strip()
    except Exception:
        return ""


def detect_from_environment() -> Optional[HostApp]:
    """Detect host app from shell environment variables."""
    term = os.environ.get("TERM_PROGRAM", "")

    if "iTerm" in term:
        path = _first_existing_path(["/Applications/iTerm.app", "~/Applications/iTerm.app"])
        return HostApp("iTerm.app", path or "/Applications/iTerm.app", "iTerm terminal")

    if term in ("Apple_Terminal", "Terminal"):
        path = "/System/Applications/Utilities/Terminal.app"
        return HostApp("Terminal.app", path, "macOS Terminal")

    if term == "WarpTerminal":
        return HostApp("Warp.app", "/Applications/Warp.app", "Warp terminal")

    # Cursor / VS Code integrated terminal
    if os.environ.get("VSCODE_PID") or os.environ.get("VSCODE_INJECTION"):
        # Prefer Cursor if installed
        cursor_path = _first_existing_path([
            "/Applications/Cursor.app",
            os.path.expanduser("~/Applications/Cursor.app"),
        ])
        if cursor_path:
            return HostApp("Cursor.app", cursor_path, "Cursor integrated terminal")

        code_path = _first_existing_path(["/Applications/Visual Studio Code.app"])
        if code_path:
            return HostApp("Visual Studio Code.app", code_path, "VS Code integrated terminal")

    if "CURSOR" in os.environ.get("TERM_SESSION_ID", "").upper():
        cursor_path = _first_existing_path([
            "/Applications/Cursor.app",
            os.path.expanduser("~/Applications/Cursor.app"),
        ])
        if cursor_path:
            return HostApp("Cursor.app", cursor_path, "Cursor")

    return None


def _get_full_command(pid: int) -> str:
    try:
        r = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return r.stdout.strip()
    except Exception:
        return ""


def detect_from_process_tree() -> Optional[HostApp]:
    """Walk up from parent process; skip shells and Python binaries."""
    pid = os.getppid()
    seen = set()

    for _ in range(40):
        if pid in seen or pid <= 1:
            break
        seen.add(pid)

        comm = _get_process_name(pid)
        cmd = _get_full_command(pid)
        comm_lower = comm.lower()

        # Skip shells and python — keep walking up to find Cursor/Terminal
        if comm_lower in SKIP_NAMES or comm_lower.startswith("python"):
            pid = _get_ppid(pid)
            continue

        # Cursor often appears in full command path
        if "cursor.app" in cmd.lower() or "cursor" in comm_lower:
            path = _first_existing_path([
                "/Applications/Cursor.app",
                os.path.expanduser("~/Applications/Cursor.app"),
            ])
            if path:
                return HostApp("Cursor.app", path, f"process tree ({comm})")

        for keyword, app_name, paths in KNOWN_APPS:
            if keyword.lower() in comm_lower:
                path = _first_existing_path(paths)
                if path:
                    return HostApp(app_name, path, f"process tree ({comm})")
                return HostApp(app_name, paths[0], f"process tree ({comm})")

        pid = _get_ppid(pid)

    return None


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_venv_python() -> Optional[Path]:
    venv_py = get_project_root() / "venv" / "bin" / "python3"
    return venv_py if venv_py.exists() else None


# Packages that must exist in THIS folder's venv (each copy of sayit is separate)
REQUIRED_PACKAGES = [
    ("pynput", "hotkeys"),
    ("pyperclip", "paste"),
    ("faster_whisper", "Whisper engine"),
    ("sounddevice", "audio capture"),
    ("rumps", "menu bar"),
]


def verify_venv_for_folder(project_root: Path) -> bool:
    """Ensure this folder has its own installed venv with all packages."""
    venv_py = project_root / "venv" / "bin" / "python3"

    if not venv_py.exists():
        print("  ✗ No venv in this folder.")
        print()
        print("  Each copy of sayit needs its own install (venv is not shared).")
        print()
        print("  Run:")
        print(f"    cd {project_root}")
        print("    ./scripts/install.sh")
        return False

    missing = []
    for module, label in REQUIRED_PACKAGES:
        result = subprocess.run(
            [str(venv_py), "-c", f"import {module}"],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            missing.append((module, label))

    if missing:
        print("  ✗ Missing packages in THIS folder's venv:")
        for module, label in missing:
            print(f"      - {module} ({label})")
        print()
        print("  Run install in this folder first:")
        print(f"    cd {project_root}")
        print("    ./scripts/install.sh")
        return False

    print("  ✓ venv OK in this folder (all packages installed)")
    return True


def ensure_using_folder_venv() -> None:
    """Re-run this script with the venv python for this folder if needed."""
    venv_py = get_venv_python()
    if not venv_py:
        return

    try:
        same = Path(sys.executable).resolve() == venv_py.resolve()
    except OSError:
        same = False

    if not same:
        print(f"  → Using this folder's venv: {venv_py}")
        print()
        os.execv(str(venv_py), [str(venv_py), str(Path(__file__).resolve())] + sys.argv[1:])


# Packages required for permission checks and SayIt runtime
REQUIRED_PACKAGES = [
    ("pynput", "hotkeys"),
    ("pyperclip", "paste"),
    ("faster_whisper", "transcription"),
    ("sounddevice", "audio"),
    ("rumps", "menu bar"),
]


def verify_venv_packages(python: Path) -> list[str]:
    """Return list of missing package descriptions."""
    missing = []
    for module, label in REQUIRED_PACKAGES:
        result = subprocess.run(
            [str(python), "-c", f"import {module}"],
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            missing.append(f"{module} ({label})")
    return missing


def ensure_venv_python() -> Path:
    """
    Ensure we run with THIS folder's venv python.
    Re-exec automatically if user called system python3.
    """
    project = get_project_root()
    venv_py = project / "venv" / "bin" / "python3"

    print(f"  SayIt folder: {project}")
    print()

    if not venv_py.exists():
        print("  ✗ No venv in this folder.")
        print()
        print("  Each copy of SayIt needs its own install (venv is not shared).")
        print()
        print("  Run in THIS folder:")
        print(f"    cd {project}")
        print("    ./scripts/install.sh")
        print()
        sys.exit(1)

    current = Path(sys.executable).resolve()
    target = venv_py.resolve()

    if current != target:
        print("  ⚠️  Not using this folder's venv — re-running with correct Python...")
        print(f"      was: {current}")
        print(f"      now: {target}")
        print()
        os.execv(str(target), [str(target)] + sys.argv)

    missing = verify_venv_packages(target)
    if missing:
        print("  ✗ Missing packages in THIS folder's venv:")
        for pkg in missing:
            print(f"      - {pkg}")
        print()
        print("  Run install in this folder:")
        print(f"    cd {project}")
        print("    ./scripts/install.sh")
        print()
        sys.exit(1)

    print("  ✓ venv OK (all packages installed in this folder)")
    print()
    return target


def detect_host_app() -> HostApp:
    """Find which macOS app needs Accessibility + Input Monitoring."""
    # Cursor integrated terminal often lacks TERM_PROGRAM — try tree first
    host = detect_from_environment() or detect_from_process_tree()

    if host:
        return host

    # If Cursor is installed, assume Cursor (common case for sh-3.2$ prompt)
    cursor_path = _first_existing_path([
        "/Applications/Cursor.app",
        os.path.expanduser("~/Applications/Cursor.app"),
    ])
    if cursor_path:
        return HostApp(
            "Cursor.app",
            cursor_path,
            "default (Cursor installed — grant Cursor.app if you use Cursor terminal)",
        )

    return HostApp(
        "Terminal.app",
        "/System/Applications/Utilities/Terminal.app",
        "default (use Terminal.app or Cursor.app)",
    )


def check_accessibility() -> Optional[bool]:
    """Check if Accessibility permission is granted."""
    try:
        from ApplicationServices import AXIsProcessTrusted
        return AXIsProcessTrusted()
    except ImportError:
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from ApplicationServices import AXIsProcessTrusted; print(AXIsProcessTrusted())",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip() == "True"
        except Exception:
            return None


def check_input_monitoring() -> Optional[bool]:
    """Check if Input Monitoring permission is granted."""
    try:
        from pynput import keyboard

        def on_press(key):
            return False

        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        time.sleep(0.15)
        listener.stop()
        return True
    except Exception as e:
        if "not trusted" in str(e).lower():
            return False
        return None


def open_accessibility_settings() -> None:
    subprocess.run([
        "open",
        "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
    ])


def open_input_monitoring_settings() -> None:
    subprocess.run([
        "open",
        "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent",
    ])


def print_add_app_instructions(host: HostApp) -> None:
    """Detailed click-by-click guide for System Settings."""
    folder = os.path.dirname(host.path)

    print()
    print("=" * 60)
    print("  HOW TO ADD THE CORRECT APP (NOT sh or python3)")
    print("=" * 60)
    print()
    print(f"  Add this application:  {host.name}")
    print(f"  Full path:             {host.path}")
    print(f"  Detected from:         {host.how_launched}")
    print()
    print("  DO NOT add: /bin/sh, python3, Python.app, or sayit — they won't work.")
    print("  For Cursor users: only Cursor.app is needed.")
    print()
    print("-" * 60)
    print("  After clicking the + button in System Settings:")
    print("-" * 60)
    print()
    print("  1. A file picker opens titled 'Applications' or similar")
    print()
    print("  2. Press  Cmd + Shift + G  (Go to Folder)")
    print()
    print(f"  3. Paste this path and press Go:")
    print(f"       {folder}")
    print()
    print(f"  4. Select  {host.name}  and click Open")
    print()
    print("  5. Back in the list, turn ON the toggle next to the app name")
    print()
    print("  6. If the app was already listed but off — just enable the toggle")
    print()
    print("-" * 60)
    print("  Which app to add (pick how YOU run SayIt):")
    print("-" * 60)
    print()
    print("  | How you run SayIt              | Add this app          |")
    print("  |--------------------------------|-----------------------|")
    print("  | Cursor built-in terminal       | Cursor.app            |")
    print("  | VS Code integrated terminal    | Visual Studio Code.app|")
    print("  | macOS Terminal app             | Terminal.app          |")
    print("  | iTerm                          | iTerm.app             |")
    print("  | Double-click run.py in Finder  | Python or Terminal    |")
    print()
    print("  Repeat the SAME app in BOTH places:")
    print("    • Privacy & Security → Accessibility")
    print("    • Privacy & Security → Input Monitoring")
    print()
    print("  Then QUIT and REOPEN Cursor/Terminal (required by macOS).")
    print()


def main() -> int:
    check_only = "--check-only" in sys.argv
    project_root = get_project_root()

    print("=" * 50)
    print("  SayIt Permission Checker")
    print("=" * 50)
    print()
    print(f"  SayIt folder: {project_root}")
    print()

    if not verify_venv_for_folder(project_root):
        return 1

    ensure_using_folder_venv()

    print()

    host = detect_host_app()
    venv_py = get_venv_python()

    print(f"Host app to authorize: {host.name}")
    print(f"Path: {host.path}")
    print(f"({host.how_launched})")
    print()
    print(f"Checker running as: {sys.executable}")
    if venv_py:
        print(f"SayIt runs as:       {venv_py}")
        print()
        print("  Grant permissions to the HOST APP above (Cursor.app),")
        print("  NOT to python3 or Python.app — those are wrong for Cursor users.")
    print()

    print("Checking Accessibility permission...")
    accessibility = check_accessibility()
    if accessibility is True:
        print("  ✅ Accessibility: GRANTED")
    elif accessibility is False:
        print("  ❌ Accessibility: NOT GRANTED")
    else:
        print("  ⚠️  Accessibility: Unable to check (install pyobjc via pip)")

    print("Checking Input Monitoring permission...")
    input_mon = check_input_monitoring()
    if input_mon is True:
        print("  ✅ Input Monitoring: GRANTED")
    elif input_mon is False:
        print("  ❌ Input Monitoring: NOT GRANTED")
    else:
        print("  ⚠️  Input Monitoring: Unable to check (grant manually)")

    print()

    if accessibility is True and input_mon is True:
        print("✅ All permissions granted! SayIt is ready to use.")
        return 0

    if check_only:
        print_add_app_instructions(host)
        return 1 if (accessibility is False or input_mon is False) else 0

    print("=" * 50)
    print("  Permission Setup Required")
    print("=" * 50)
    print_add_app_instructions(host)

    if accessibility is not True:
        print("📋 STEP 1: Accessibility")
        input("   Press Enter to open System Settings → Accessibility...")
        open_accessibility_settings()
        print(f"   → Add {host.name} using the steps above.")
        input("   Press Enter when done...")
        print()

    if input_mon is not True:
        print("📋 STEP 2: Input Monitoring")
        input("   Press Enter to open System Settings → Input Monitoring...")
        open_input_monitoring_settings()
        print(f"   → Add the SAME app: {host.name}")
        input("   Press Enter when done...")
        print()

    print("Verifying permissions...")
    print("  (Restart Cursor/Terminal first if you just granted access)")
    print()
    accessibility = check_accessibility()
    input_mon = check_input_monitoring()

    if accessibility is True and input_mon is True:
        print("✅ All permissions granted! Start with: ./scripts/start.sh")
        return 0

    print("⚠️  Some permissions may still be missing.")
    print()
    print("   Try this:")
    print("   1. Quit Cursor or Terminal completely (Cmd+Q)")
    print("   2. Reopen it")
    print("   3. Run: ./scripts/start.sh")
    print("   4. Run this checker again")
    return 1


if __name__ == "__main__":
    sys.exit(main())
