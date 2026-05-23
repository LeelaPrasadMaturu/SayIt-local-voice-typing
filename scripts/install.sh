#!/bin/bash
# SayIt Installation Script
# One-command setup for local voice typing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python3"
VENV_PIP="$VENV_DIR/bin/pip"
LOG_FILE="$PROJECT_DIR/logs/install.log"
TOTAL_STEPS=4

mkdir -p "$PROJECT_DIR/logs"
: > "$LOG_FILE"

# --- Progress helpers ---
progress_bar() {
    local current=$1
    local total=$2
    local width=24
    local filled=$((current * width / total))
    local empty=$((width - filled))
    printf "  ["
    printf "%${filled}s" "" | tr ' ' '='
    printf "%${empty}s" "" | tr ' ' ' '
    printf "] %d/%d\n" "$current" "$total"
}

step_header() {
    local step=$1
    local title=$2
    echo ""
    progress_bar "$step" "$TOTAL_STEPS"
    echo "  $title"
    echo "  $(printf '%.0s-' {1..40})"
}

step_ok() {
    echo "  ✓ $1"
}

step_info() {
    echo "  → $1"
}

run_logged() {
    # Run command, show output live, also append to log
    "$@" 2>&1 | tee -a "$LOG_FILE"
    return "${PIPESTATUS[0]}"
}

# --- Banner ---
echo "=================================================="
echo "  SayIt Installer"
echo "  Local Voice Typing for macOS"
echo "=================================================="
echo ""

# Check macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: SayIt currently only supports macOS"
    exit 1
fi

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Install via: brew install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
step_ok "Found Python $PYTHON_VERSION"

export PIP_ROOT_USER_ACTION=ignore
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_PROGRESS_BAR=on

# --- Step 1: venv ---
step_header 1 "Creating virtual environment"

if [ -d "$VENV_DIR" ]; then
    step_ok "Virtual environment already exists"
else
    step_info "Creating venv at $VENV_DIR ..."
    if run_logged python3 -m venv "$VENV_DIR"; then
        step_ok "Virtual environment created"
    else
        echo "  ✗ Failed to create venv. See: $LOG_FILE"
        exit 1
    fi
fi

# All installs go INTO venv (not system Python)
if [ ! -f "$VENV_PYTHON" ]; then
    echo "  ✗ venv python missing after create. See: $LOG_FILE"
    exit 1
fi
step_ok "Using venv Python: $VENV_PYTHON"

# --- Step 2: dependencies (into venv only) ---
step_header 2 "Installing dependencies into venv"
step_info "Upgrading pip in venv..."
if run_logged "$VENV_PIP" install --upgrade pip --no-warn-script-location; then
    step_ok "pip upgraded"
else
    echo "  ✗ pip upgrade failed. See: $LOG_FILE"
    exit 1
fi

# Install each package with visible progress
REQ_FILE="$PROJECT_DIR/requirements.txt"
PKG_COUNT=$(grep -vE '^\s*#|^\s*$' "$REQ_FILE" | wc -l | tr -d ' ')
PKG_NUM=0

step_info "Installing $PKG_COUNT packages (progress bar below)..."
echo ""

while IFS= read -r line || [ -n "$line" ]; do
    # Skip comments and blank lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue

    PKG_NUM=$((PKG_NUM + 1))
    PKG_NAME="${line%%[*><= ]*}"  # strip version specifiers
    PKG_NAME="${PKG_NAME%%#*}"

    echo "  [$PKG_NUM/$PKG_COUNT] $PKG_NAME"
    if run_logged "$VENV_PIP" install "$line" --no-warn-script-location; then
        step_ok "$PKG_NAME installed"
    else
        echo ""
        echo "  ✗ Failed to install: $PKG_NAME"
        echo "  See: $LOG_FILE"
        echo ""
        echo "  Common fix: xcode-select --install"
        exit 1
    fi
    echo ""
done < "$REQ_FILE"

step_ok "All dependencies installed"

# --- Step 3: verify ---
step_header 3 "Verifying installation"

VERIFY_PKGS=(
    "faster_whisper:Whisper engine"
    "pynput:Hotkey listener"
    "sounddevice:Audio capture"
    "rumps:Menu bar"
    "pyperclip:Clipboard paste"
)

for entry in "${VERIFY_PKGS[@]}"; do
    module="${entry%%:*}"
    label="${entry##*:}"
    step_info "Checking $label ($module)..."
    if "$VENV_PYTHON" -c "import $module" 2>>"$LOG_FILE"; then
        step_ok "$label OK"
    else
        echo "  ✗ $label failed to import. See: $LOG_FILE"
        exit 1
    fi
done

step_ok "All core packages verified"

# --- Step 4: permissions ---
step_header 4 "Checking macOS permissions"

if "$VENV_PYTHON" "$SCRIPT_DIR/check_permissions.py" --check-only 2>>"$LOG_FILE"; then
    step_ok "Input Monitoring & Accessibility granted"
else
    step_info "Permissions need one-time setup"
    echo ""
    echo "  Run after install:"
    echo "    $VENV_PYTHON $SCRIPT_DIR/check_permissions.py"
    echo ""
fi

# --- Done ---
progress_bar "$TOTAL_STEPS" "$TOTAL_STEPS"
echo ""
echo "=================================================="
echo "  Installation Complete!"
echo "=================================================="
echo ""

read -p "Enable auto-start at login? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    "$SCRIPT_DIR/autostart.sh" install
fi

echo ""
echo "Packages are in: $VENV_DIR"
echo "You do NOT need to run 'source venv/bin/activate' — start.sh uses venv automatically."
echo ""
echo "To start SayIt:"
echo "  ./scripts/start.sh"
echo ""
echo "Usage:"
echo "  1. Hold Ctrl + . (period)"
echo "  2. Speak"
echo "  3. Release - text appears at cursor"
echo ""
echo "Full install log: $LOG_FILE"
echo ""
