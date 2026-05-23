#!/usr/bin/env python3
"""Quick start script for SayIt."""

import atexit
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PID_FILE = PROJECT_ROOT / ".sayit.pid"

src_path = PROJECT_ROOT / "src"
sys.path.insert(0, str(src_path))

# Enable terminal debug logs by default for local testing.
# Set SAYIT_DEBUG=0 before running to quiet these logs.
os.environ.setdefault("SAYIT_DEBUG", "1")


def _write_pid_file() -> None:
    PID_FILE.write_text(str(os.getpid()))


def _remove_pid_file() -> None:
    try:
        PID_FILE.unlink(missing_ok=True)
    except OSError:
        pass


atexit.register(_remove_pid_file)

from main import main

if __name__ == "__main__":
    _write_pid_file()

    debug_enabled = os.environ.get("SAYIT_DEBUG", "0").lower() not in {
        "0",
        "false",
        "no",
        "off",
    }
    print(f"[debug][run] starting run.py debug={'on' if debug_enabled else 'off'}")
    print(f"[debug][run] pid={os.getpid()} project={PROJECT_ROOT}")
    main()
