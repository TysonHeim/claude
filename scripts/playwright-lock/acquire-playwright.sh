#!/bin/bash
# Playwright Instance Lock Acquisition
# Acquires exclusive lock on an available Playwright MCP instance
#
# Usage: ./acquire-playwright.sh [--wait] [--prefer <instance>] [--timeout <minutes>]
#
# Exit codes:
#   0 - Lock acquired (instance name printed to stdout)
#   1 - All instances locked
#   2 - Invalid arguments

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
log_lock() { echo -e "${BLUE}[LOCK]${NC} $1" >&2; }

# Configuration
INSTANCES="${PLAYWRIGHT_INSTANCES:-playwright-1,playwright-2,playwright-3}"
LOCK_DIR="${PLAYWRIGHT_LOCK_DIR:-/tmp/playwright-locks}"
DEFAULT_TIMEOUT="${PLAYWRIGHT_LOCK_TIMEOUT:-30}"
STALE_THRESHOLD=60  # Minutes before lock is stale

# Parse arguments
WAIT_MODE=false
PREFERRED=""
LOCK_TIMEOUT=$DEFAULT_TIMEOUT

while [[ $# -gt 0 ]]; do
    case $1 in
        --wait)
            WAIT_MODE=true
            shift
            ;;
        --prefer)
            PREFERRED="$2"
            shift 2
            ;;
        --timeout)
            LOCK_TIMEOUT="$2"
            shift 2
            ;;
        -*)
            log_error "Unknown option: $1"
            exit 2
            ;;
        *)
            log_error "Unexpected argument: $1"
            exit 2
            ;;
    esac
done

# Ensure lock directory exists
mkdir -p "$LOCK_DIR"

# Get agent identifier (stable across bash invocations)
get_stable_agent_id() {
    if [ -n "$CLAUDE_AGENT_ID" ]; then
        echo "$CLAUDE_AGENT_ID"
    elif [ -n "$TERM_SESSION_ID" ]; then
        echo "term-${TERM_SESSION_ID}"
    elif tty_device=$(tty 2>/dev/null) && [ "$tty_device" != "not a tty" ]; then
        echo "tty-$(echo "$tty_device" | tr '/' '-')"
    else
        echo "cwd-$(basename "$(pwd)")"
    fi
}
AGENT_ID=$(get_stable_agent_id)

# Check if lock is stale
is_lock_stale() {
    local lock_file="$1"
    if [ ! -f "$lock_file" ]; then
        return 0
    fi

    local acquired_at=$(grep -oE '"acquired_at":[[:space:]]*[0-9]+' "$lock_file" 2>/dev/null | grep -o '[0-9]*')
    if [ -z "$acquired_at" ]; then
        return 0
    fi

    local now=$(date +%s)
    local age_minutes=$(( (now - acquired_at) / 60 ))

    [ $age_minutes -gt $STALE_THRESHOLD ]
}

# Get lock holder
get_lock_holder() {
    local lock_file="$1"
    grep -oE '"holder":[[:space:]]*"[^"]*"' "$lock_file" 2>/dev/null | sed 's/"holder":[[:space:]]*"\([^"]*\)"/\1/' || echo ""
}

# Try to acquire lock for instance
try_acquire_lock() {
    local instance="$1"
    local lock_file="$LOCK_DIR/${instance}.lock"
    local now=$(date +%s)
    local expires_at=$((now + LOCK_TIMEOUT * 60))

    if [ -f "$lock_file" ]; then
        local holder=$(get_lock_holder "$lock_file")

        if [ "$holder" = "$AGENT_ID" ]; then
            log_info "Refreshing existing lock on $instance"
        elif is_lock_stale "$lock_file"; then
            log_warn "Overriding stale lock on $instance (was: $holder)"
        else
            return 1
        fi
    fi

    cat > "$lock_file" << EOF
{
    "holder": "$AGENT_ID",
    "instance": "$instance",
    "acquired_at": $now,
    "expires_at": $expires_at,
    "timeout_minutes": $LOCK_TIMEOUT,
    "pid": $$,
    "cwd": "$(pwd)"
}
EOF

    return 0
}

# Main acquisition logic
acquire_instance() {
    IFS=',' read -ra INSTANCE_ARRAY <<< "$INSTANCES"

    if [ -n "$PREFERRED" ]; then
        if try_acquire_lock "$PREFERRED"; then
            echo "$PREFERRED"
            return 0
        fi
        log_warn "Preferred instance $PREFERRED not available"
    fi

    for instance in "${INSTANCE_ARRAY[@]}"; do
        if try_acquire_lock "$instance"; then
            echo "$instance"
            return 0
        fi
    done

    return 1
}

# Main execution
log_lock "Acquiring Playwright instance..." >&2
log_info "Agent ID: $AGENT_ID" >&2
echo "" >&2

if [ "$WAIT_MODE" = true ]; then
    attempt=1
    max_wait=300
    while true; do
        if instance=$(acquire_instance); then
            log_info "Lock acquired: $instance" >&2
            echo "==========================================" >&2
            echo "Playwright instance ready: $instance" >&2
            echo "Use MCP tools: mcp__${instance}__*" >&2
            echo "Release when done: release-playwright.sh" >&2
            echo "==========================================" >&2
            echo "$instance"
            exit 0
        fi

        if [ $attempt -gt $max_wait ]; then
            log_error "Timeout waiting for Playwright instance"
            exit 1
        fi

        log_lock "All instances locked. Waiting... (attempt $attempt)" >&2
        sleep 1
        attempt=$((attempt + 1))
    done
else
    if instance=$(acquire_instance); then
        log_info "Lock acquired: $instance" >&2
        echo "==========================================" >&2
        echo "Playwright instance ready: $instance" >&2
        echo "Use MCP tools: mcp__${instance}__*" >&2
        echo "Release when done: release-playwright.sh" >&2
        echo "==========================================" >&2
        echo "$instance"
        exit 0
    else
        log_error "All Playwright instances are locked"
        echo "" >&2
        echo "Options:" >&2
        echo "  1. Wait for instance: $0 --wait" >&2
        echo "  2. Check status:      playwright-status.sh" >&2
        echo "  3. Force release:     release-playwright.sh --force <instance>" >&2
        exit 1
    fi
fi
