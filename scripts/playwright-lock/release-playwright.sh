#!/bin/bash
# Playwright Instance Lock Release
# Releases lock on Playwright MCP instance
#
# Usage: ./release-playwright.sh [--force <instance>]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
INSTANCES="${PLAYWRIGHT_INSTANCES:-playwright-1,playwright-2,playwright-3}"
LOCK_DIR="${PLAYWRIGHT_LOCK_DIR:-/tmp/playwright-locks}"

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

# Parse arguments
FORCE_INSTANCE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_INSTANCE="$2"
            shift 2
            ;;
        *)
            log_error "Unknown argument: $1"
            exit 2
            ;;
    esac
done

get_lock_holder() {
    local lock_file="$1"
    grep -oE '"holder":[[:space:]]*"[^"]*"' "$lock_file" 2>/dev/null | sed 's/"holder":[[:space:]]*"\([^"]*\)"/\1/' || echo ""
}

# Force release specific instance
if [ -n "$FORCE_INSTANCE" ]; then
    lock_file="$LOCK_DIR/${FORCE_INSTANCE}.lock"
    if [ -f "$lock_file" ]; then
        holder=$(get_lock_holder "$lock_file")
        log_warn "Force releasing $FORCE_INSTANCE (was held by: $holder)"
        rm -f "$lock_file"
        log_info "Released: $FORCE_INSTANCE"
    else
        log_info "$FORCE_INSTANCE was not locked"
    fi
    exit 0
fi

# Release locks owned by current agent
IFS=',' read -ra INSTANCE_ARRAY <<< "$INSTANCES"
released=0

for instance in "${INSTANCE_ARRAY[@]}"; do
    lock_file="$LOCK_DIR/${instance}.lock"
    if [ -f "$lock_file" ]; then
        holder=$(get_lock_holder "$lock_file")
        if [ "$holder" = "$AGENT_ID" ]; then
            rm -f "$lock_file"
            log_info "Released: $instance"
            released=$((released + 1))
        fi
    fi
done

if [ $released -eq 0 ]; then
    log_warn "No locks held by this terminal (Agent ID: $AGENT_ID)"
    log_info "Use --force <instance> to release a specific lock"
else
    log_info "Released $released instance(s)"
fi
