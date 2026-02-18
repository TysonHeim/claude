#!/bin/bash
# Track agent and skill usage for status line display
# Called by PostToolUse hook for Task and Skill tool invocations
# Supports parallel Claude terminals via per-session state files

STATE_DIR="$HOME/.claude/sessions"
input=$(cat)

# Get tool name and input from hook data
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
tool_input=$(echo "$input" | jq -r '.tool_input // empty')
session_id=$(echo "$input" | jq -r '.session_id // empty')

# Create sessions directory if needed
mkdir -p "$STATE_DIR"

# Use session-specific state file
STATE_FILE="$STATE_DIR/session-${session_id}.json"

# Initialize session state file if it doesn't exist
if [ ! -f "$STATE_FILE" ]; then
    start_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    echo "{\"agents\":0,\"skills\":0,\"agent_types\":{},\"skill_names\":{},\"session_id\":\"$session_id\",\"session_start\":\"$start_time\"}" > "$STATE_FILE"
fi

# Clean up old session files (older than 24 hours)
find "$STATE_DIR" -name "session-*.json" -mmin +1440 -delete 2>/dev/null

# Increment appropriate counter and track specific types
if [ "$tool_name" = "Task" ]; then
    # Extract subagent_type from tool input
    agent_type=$(echo "$tool_input" | jq -r '.subagent_type // "unknown"' 2>/dev/null)
    if [ -z "$agent_type" ] || [ "$agent_type" = "null" ]; then
        agent_type="unknown"
    fi

    # Increment total and specific agent type count
    jq --arg type "$agent_type" '
        .agents += 1 |
        .agent_types[$type] = ((.agent_types[$type] // 0) + 1)
    ' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

elif [ "$tool_name" = "Skill" ]; then
    # Extract skill name from tool input
    skill_name=$(echo "$tool_input" | jq -r '.skill // "unknown"' 2>/dev/null)
    if [ -z "$skill_name" ] || [ "$skill_name" = "null" ]; then
        skill_name="unknown"
    fi

    # Increment total and specific skill name count
    jq --arg name "$skill_name" '
        .skills += 1 |
        .skill_names[$name] = ((.skill_names[$name] // 0) + 1)
    ' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
fi

exit 0
