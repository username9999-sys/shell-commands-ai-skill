#!/usr/bin/env bash
# run_sandbox.sh - Execute command in sandbox container
# Usage: ./run_sandbox.sh "command" [args...]

set -euo pipefail

IMAGE_NAME="shell-skill-sandbox"
CONTAINER_NAME="shell-skill-sandbox-$(date +%s)"

# Check if image exists, build if not
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo "Building sandbox image..."
    docker build -t "$IMAGE_NAME" "$(dirname "$0")"
fi

# Security: Validate command against blacklist
BLACKLIST=(
    "rm -rf /"
    "rm -rf /*"
    "dd if=/dev/zero of=/dev/sd"
    "dd if=/dev/random of=/dev/sd"
    "mkfs"
    "fdisk /dev/sd"
    "parted /dev/sd"
    "iptables -F"
    "iptables -X"
    "ufw disable"
    "curl | sh"
    "wget | sh"
    "curl | bash"
    "bash -c \"\$(curl"
    "chmod 777 /"
    "chown -R root:root /"
    "mv / /dev/null"
    ":(){ :|:& };:"
)

CMD_STR="$*"
for pattern in "${BLACKLIST[@]}"; do
    if [[ "$CMD_STR" == *"$pattern"* ]]; then
        echo "ERROR: Command matches blacklist pattern: $pattern" >&2
        exit 1
    fi
done

# Run in sandbox with security constraints
docker run --rm \
    --name "$CONTAINER_NAME" \
    --network=none \
    --cpus=0.5 \
    --memory=128m \
    --pids-limit=50 \
    --security-opt=no-new-privileges:true \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid,size=50m \
    --tmpfs /workspace:rw,noexec,nosuid,size=100m \
    -v "$(pwd):/workspace:ro" \
    -u 1000:1000 \
    --cap-drop=ALL \
    "$IMAGE_NAME" \
    "$@"