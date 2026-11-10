#!/bin/sh

# Trap SIGTERM and SIGINT, then tell Asterisk to stop gracefully via CLI
_term() {
    echo "Caught shutdown signal, requesting graceful stop from Asterisk..."
    asterisk -rx "core stop gracefully"
    
    # Wait a moment for the child process to exit cleanly after taking the command
    wait "$child" 2>/dev/null
}

trap _term TERM INT

# Start asterisk in the foreground
asterisk -f &

# Capture the PID of the background process
child=$!

# Wait for the asterisk process to exit
wait "$child"
