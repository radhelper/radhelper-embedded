#!/bin/bash

# Name of the tmux session
SESSION_NAME="monitor"

# Check if the session already exists
tmux has-session -t $SESSION_NAME 2>/dev/null

# If the session exists, kill it
if [ $? == 0 ]; then
    echo "Session $SESSION_NAME already exists. Killing it..."
    tmux kill-session -t $SESSION_NAME
fi

# Create a new tmux session with the first window
echo "Creating new session: $SESSION_NAME"
tmux new-session -d -s $SESSION_NAME -n "PowerS" "cat /tmp/logger_PowerS"

# # Create additional windows (from window 1 to window 6)
# for i in {1..6}; do
#     tmux new-window -t $SESSION_NAME -n "dut$i" "cat /tmp/logger_dut$i"
# done

# Attach to the session
tmux attach-session -t $SESSION_NAME
