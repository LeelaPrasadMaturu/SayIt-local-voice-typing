#!/bin/bash
# Start SayIt

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python3"
PID_FILE="$PROJECT_DIR/.sayit.pid"

is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
        rm -f "$PID_FILE"
    fi
    return 1
}

if is_running; then
    echo "SayIt is already running (PID: $(cat "$PID_FILE"))"
    echo "Use ./scripts/stop.sh to stop it first"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found."
    echo "Run from this folder: $PROJECT_DIR"
    echo "  ./scripts/install.sh"
    exit 1
fi

if [ ! -f "$VENV_PYTHON" ]; then
    echo "venv python not found. Re-run: ./scripts/install.sh"
    exit 1
fi

echo "Starting SayIt..."
echo "  Project: $PROJECT_DIR"
cd "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/logs"

# Use venv python explicitly (same binary every time)
nohup "$VENV_PYTHON" run.py >> "$PROJECT_DIR/logs/sayit.log" 2>&1 &

# Wait for app to write .sayit.pid (up to 15 seconds)
WAIT=0
while [ "$WAIT" -lt 15 ]; do
    if is_running; then
        echo "SayIt started! (PID: $(cat "$PID_FILE"))"
        echo ""
        echo "  Look for the SayIt icon in your menu bar (top-right)."
        echo ""
        echo "Usage: Hold Ctrl + . to record, release to transcribe"
        echo "Stop:  ./scripts/stop.sh"
        echo "Logs:  $PROJECT_DIR/logs/sayit.log"
        exit 0
    fi
    sleep 1
    WAIT=$((WAIT + 1))
done

echo "Failed to start SayIt (no PID file after 15s)."
echo ""
echo "Check the log for errors:"
echo "  tail -30 $PROJECT_DIR/logs/sayit.log"
echo ""
echo "Try running in foreground to see errors:"
echo "  cd $PROJECT_DIR && source venv/bin/activate && python run.py"
echo ""
echo "If you see permission errors, grant access to Cursor.app (not sh):"
echo "  $VENV_PYTHON $SCRIPT_DIR/check_permissions.py"
exit 1
