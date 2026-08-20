#!/usr/bin/env bash
# fetch_man.sh - Fetch man pages for commands (parallel)
# Usage: ./fetch_man.sh [command...] or ./fetch_man.sh --list <file> or ./fetch_man.sh --parallel N

set -euo pipefail

RAW_DIR="data/raw"
MAN7_BASE="https://man7.org/linux/man-pages/man1"
GNU_BASE="https://www.gnu.org/software"

mkdir -p "$RAW_DIR"

# Default commands if none provided
DEFAULT_COMMANDS=(
    find grep ls cp mv rm mkdir rmdir cat head tail less more
    sed awk sort uniq cut tr wc xargs
    which whereis type alias unalias history
    ps top kill jobs bg fg nohup disown wait
    date cal bc dc factor seq yes tee
    env printenv export set unset declare
    ssh scp rsync curl wget tar gzip gunzip
    chmod chown chgrp umask stat file
    df du free uptime who whoami id groups
    ping traceroute netstat ss ip dig nslookup
    git make cmake gcc g++ clang python3 node
    docker kubectl helm terraform ansible
)

# Default parallelism
PARALLEL_JOBS=4

show_usage() {
    cat <<EOF
Usage: $0 [OPTIONS] [command...]

Options:
  -p, --parallel N    Number of parallel jobs (default: 4)
  -l, --list FILE     Read commands from file (one per line)
  -h, --help          Show this help

Examples:
  $0                           # Fetch default commands with 4 parallel jobs
  $0 -p 8 find grep ls         # Fetch 3 commands with 8 parallel jobs
  $0 --list commands.txt       # Fetch commands from file
EOF
}

fetch_local() {
    local cmd="$1"
    local output="$RAW_DIR/$cmd.txt"
    
    if man -P cat "$cmd" > "$output" 2>/dev/null; then
        echo "✓ Local: $cmd"
        return 0
    fi
    return 1
}

fetch_man7() {
    local cmd="$1"
    local output="$RAW_DIR/$cmd.txt"
    local url="$MAN7_BASE/$cmd.1.html"
    
    if curl -sLf --max-time 10 "$url" | \
        sed -n '/<div class="main">/,/<\/div>/p' | \
        sed 's/<[^>]*>//g' | \
        sed '/^$/d' > "$output" 2>/dev/null; then
        if [[ -s "$output" ]]; then
            echo "✓ man7.org: $cmd"
            return 0
        fi
    fi
    rm -f "$output"
    return 1
}

fetch_gnu() {
    local cmd="$1"
    local output="$RAW_DIR/$cmd.txt"
    
    # Try common GNU packages
    for pkg in coreutils bash findutils grep sed gawk coreutils; do
        local url="https://www.gnu.org/software/$pkg/manual/html_node/${cmd}.html"
        if curl -sLf --max-time 10 "$url" | \
            sed -n '/<div class="node">/,/<\/div>/p' | \
            sed 's/<[^>]*>//g' | \
            sed '/^$/d' > "$output" 2>/dev/null; then
            if [[ -s "$output" ]]; then
                echo "✓ GNU $pkg: $cmd"
                return 0
            fi
        fi
        rm -f "$output"
    done
    return 1
}

fetch_command() {
    local cmd="$1"
    echo -n "Fetching $cmd... "
    
    if fetch_local "$cmd"; then
        return 0
    elif fetch_man7 "$cmd"; then
        return 0
    elif fetch_gnu "$cmd"; then
        return 0
    else
        echo "✗ Failed: $cmd"
        return 1
    fi
}

# Export functions for parallel execution
export -f fetch_local fetch_man7 fetch_gnu fetch_command
export RAW_DIR MAN7_BASE GNU_BASE

# Main
parse_args() {
    COMMANDS=()
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--parallel)
                PARALLEL_JOBS="$2"
                shift 2
                ;;
            -l|--list)
                if [[ -f "$2" ]]; then
                    mapfile -t COMMANDS < "$2"
                else
                    echo "Error: File $2 not found" >&2
                    exit 1
                fi
                shift 2
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                COMMANDS+=("$1")
                shift
                ;;
        esac
    done
    
    # Use defaults if no commands provided
    if [[ ${#COMMANDS[@]} -eq 0 ]]; then
        COMMANDS=("${DEFAULT_COMMANDS[@]}")
    fi
}

main() {
    parse_args "$@"
    
    echo "Fetching man pages for ${#COMMANDS[@]} commands with $PARALLEL_JOBS parallel jobs..."
    echo "Output directory: $RAW_DIR"
    echo
    
    mkdir -p "$RAW_DIR"
    
    # Use xargs for parallel execution
    printf '%s\n' "${COMMANDS[@]}" | xargs -P "$PARALLEL_JOBS" -I {} bash -c 'fetch_command "$@"' _ {}
    
    # Count failures
    failed=0
    for cmd in "${COMMANDS[@]}"; do
        if [[ ! -s "$RAW_DIR/$cmd.txt" ]]; then
            ((failed++))
        fi
    done
    
    echo
    echo "Done. Failed: $failed/${#COMMANDS[@]}"
    
    # Create metadata
    cat > "$RAW_DIR/.metadata.json" <<EOF
{
    "fetched_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "total": ${#COMMANDS[@]},
    "failed": $failed,
    "parallel_jobs": $PARALLEL_JOBS,
    "commands": $(printf '%s\n' "${COMMANDS[@]}" | jq -R . | jq -s .)
}
EOF
}

main "$@"