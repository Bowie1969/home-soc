#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -f bait_key ]]; then
    echo "Generating bait SSH key first..."
    ./gen-key.sh
fi

# Ensure Cowrie (UID 999 in the container) can write host keys and logs.
mkdir -p cowrie-logs cowrie-data/keys
chmod 777 cowrie-logs cowrie-data

# Prefer podman; fall back to docker.
if command -v podman-compose >/dev/null 2>&1; then
    RUN="podman-compose"
elif command -v podman >/dev/null 2>&1; then
    RUN="podman compose"
elif command -v docker-compose >/dev/null 2>&1; then
    RUN="docker-compose"
else
    RUN="docker compose"
fi

echo "Starting Cowrie honeypot with: $RUN"
$RUN up -d

echo ""
echo "Honeypot is running on localhost:2222"
echo "Live log: ./watch.py"
echo "Stop:     ./stop.sh"
