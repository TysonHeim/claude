#!/bin/bash
# Playwright Instance Status
# Shows status of all Playwright MCP instances
#
# Usage: ./playwright-status.sh [--json]

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
INSTANCES="${PLAYWRIGHT_INSTANCES:-playwright-1,playwright-2,playwright-3}"
LOCK_DIR="${PLAYWRIGHT_LOCK_DIR:-/tmp/playwright-locks}"
STALE_THRESHOLD=60

JSON_MODE=false
[ "$1" = "--json" ] && JSON_MODE=true

is_lock_stale() {
    local lock_file="$1"
    local acquired_at=$(grep -oE '"acquired_at":[[:space:]]*[0-9]+' "$lock_file" 2>/dev/null | grep -o '[0-9]*')
    [ -z "$acquired_at" ] && return 0
    local now=$(date +%s)
    local age_minutes=$(( (now - acquired_at) / 60 ))
    [ $age_minutes -gt $STALE_THRESHOLD ]
}

get_field() {
    local lock_file="$1"
    local field="$2"
    grep -oE "\"$field\":[[:space:]]*\"[^\"]*\"" "$lock_file" 2>/dev/null | sed "s/\"$field\":[[:space:]]*\"\([^\"]*\)\"/\1/" || echo ""
}

get_num_field() {
    local lock_file="$1"
    local field="$2"
    grep -oE "\"$field\":[[:space:]]*[0-9]+" "$lock_file" 2>/dev/null | grep -o '[0-9]*' || echo ""
}

IFS=',' read -ra INSTANCE_ARRAY <<< "$INSTANCES"

if [ "$JSON_MODE" = true ]; then
    echo "{"
    echo "  \"instances\": ["
    first=true
    for instance in "${INSTANCE_ARRAY[@]}"; do
        lock_file="$LOCK_DIR/${instance}.lock"
        [ "$first" = true ] || echo ","
        first=false

        if [ -f "$lock_file" ]; then
            holder=$(get_field "$lock_file" "holder")
            acquired=$(get_num_field "$lock_file" "acquired_at")
            stale="false"
            is_lock_stale "$lock_file" && stale="true"

            echo "    {"
            echo "      \"name\": \"$instance\","
            echo "      \"status\": \"locked\","
            echo "      \"holder\": \"$holder\","
            echo "      \"acquired_at\": $acquired,"
            echo "      \"stale\": $stale"
            echo -n "    }"
        else
            echo "    {"
            echo "      \"name\": \"$instance\","
            echo "      \"status\": \"available\""
            echo -n "    }"
        fi
    done
    echo ""
    echo "  ]"
    echo "}"
else
    echo ""
    echo "Playwright MCP Instance Status"
    echo "==============================="
    echo ""

    available=0
    locked=0

    for instance in "${INSTANCE_ARRAY[@]}"; do
        lock_file="$LOCK_DIR/${instance}.lock"

        if [ -f "$lock_file" ]; then
            holder=$(get_field "$lock_file" "holder")
            acquired=$(get_num_field "$lock_file" "acquired_at")
            now=$(date +%s)
            age_minutes=$(( (now - acquired) / 60 ))

            if is_lock_stale "$lock_file"; then
                echo -e "${YELLOW}Warning${NC} $instance: ${YELLOW}STALE${NC} (locked ${age_minutes}m ago by $holder)"
            else
                echo -e "${RED}Locked${NC} $instance: ${RED}LOCKED${NC} (${age_minutes}m ago by $holder)"
                locked=$((locked + 1))
            fi
        else
            echo -e "${GREEN}OK${NC} $instance: ${GREEN}AVAILABLE${NC}"
            available=$((available + 1))
        fi
    done

    echo ""
    echo "Summary: $available available, $locked locked"
    echo ""
fi
