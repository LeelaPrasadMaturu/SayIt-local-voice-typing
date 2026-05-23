#!/bin/bash
# SayIt Auto-Start Manager
# Manages Launch Agent for starting SayIt at login

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.sayit.agent.plist"
PLIST_PATH="$LAUNCH_AGENT_DIR/$PLIST_NAME"

create_plist() {
    cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sayit.agent</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/venv/bin/python3</string>
        <string>$PROJECT_DIR/run.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/sayit.log</string>
    
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/sayit.error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF
}

install_agent() {
    echo "Installing SayIt auto-start..."
    
    # Create LaunchAgents directory if needed
    mkdir -p "$LAUNCH_AGENT_DIR"
    mkdir -p "$PROJECT_DIR/logs"
    
    # Create the plist file
    create_plist
    
    # Load the agent
    launchctl unload "$PLIST_PATH" 2>/dev/null
    launchctl load "$PLIST_PATH"
    
    echo "✅ Auto-start enabled!"
    echo "   SayIt will start automatically at login."
    echo ""
    echo "   To start now: launchctl start com.sayit.agent"
    echo "   To disable:   $0 uninstall"
}

uninstall_agent() {
    echo "Removing SayIt auto-start..."
    
    if [ -f "$PLIST_PATH" ]; then
        launchctl unload "$PLIST_PATH" 2>/dev/null
        rm -f "$PLIST_PATH"
        echo "✅ Auto-start disabled!"
    else
        echo "Auto-start was not enabled."
    fi
}

status_agent() {
    if [ -f "$PLIST_PATH" ]; then
        echo "Auto-start: ENABLED"
        echo "Plist: $PLIST_PATH"
        echo ""
        echo "Status:"
        launchctl list | grep sayit || echo "  Not currently loaded"
    else
        echo "Auto-start: DISABLED"
    fi
}

case "$1" in
    install)
        install_agent
        ;;
    uninstall|remove)
        uninstall_agent
        ;;
    status)
        status_agent
        ;;
    *)
        echo "SayIt Auto-Start Manager"
        echo ""
        echo "Usage: $0 {install|uninstall|status}"
        echo ""
        echo "Commands:"
        echo "  install    Enable auto-start at login"
        echo "  uninstall  Disable auto-start"
        echo "  status     Check current status"
        ;;
esac
