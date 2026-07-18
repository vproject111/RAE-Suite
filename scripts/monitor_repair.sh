#!/bin/bash
# monitor_repair.sh
# Checks if mass_repair.py is running, and restarts it if it crashed or stopped.

LOG_FILE="/home/grzegorz/cloud/RAE-Suite/monitor_repair.log"
SCRIPT_PATH="packages/rae-quality/mass_repair.py"
PYTHON_VENV="/home/grzegorz/cloud/RAE-Suite/venv/bin/python3"

# Check if mass_repair.py is currently running
PID=$(pgrep -f "$SCRIPT_PATH")

if [ -n "$PID" ]; then
    echo "$(date): mass_repair.py is running with PID $PID." >> "$LOG_FILE"
else
    echo "$(date): mass_repair.py is NOT running! Restarting..." >> "$LOG_FILE"
    
    cd /home/grzegorz/cloud/RAE-Suite
    nohup "$PYTHON_VENV" "$SCRIPT_PATH" >> "$LOG_FILE" 2>&1 &
    
    NEW_PID=$!
    echo "$(date): Restarted mass_repair.py with PID $NEW_PID." >> "$LOG_FILE"
fi
