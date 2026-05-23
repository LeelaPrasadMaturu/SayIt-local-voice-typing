#!/bin/bash
# Stop SayIt

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/.sayit.pid"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python3"

STOPPED=0

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
        echo "Stopping SayIt (PID: $PID)..."
        kill "$PID" 2>/dev/null
        sleep 2
        if ps -p "$PID" > /dev/null 2>&1; then
            kill -9 "$PID" 2>/dev/null
        fi
        STOPPED=1
    fi
    rm -f "$PID_FILE"
fi

# Fallback: kill run.py in this project only (match working directory)
if [ -f "$VENV_PYTHON" ]; then
    for pid in $(pgrep -f "run.py" 2>/dev/null); do
        cwd=$(lsof -p "$pid" 2>/dev/null | awk '$4=="cwd" {print $9; exit}')
        if [ "$cwd" = "$PROJECT_DIR" ]; then
            kill "$pid" 2>/dev/null
            STOPPED=1
        fi
    done
fi

if [ "$STOPPED" -eq 1 ]; then
    echo "SayIt stopped."
else
    echo "SayIt is not running."
fi
