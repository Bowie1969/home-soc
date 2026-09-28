#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if command -v podman-compose >/dev/null 2>&1; then
    RUN="podman-compose"
elif command -v podman >/dev/null 2>&1; then
    RUN="podman compose"
elif command -v docker-compose >/dev/null 2>&1; then
    RUN="docker-compose"
else
    RUN="docker compose"
fi

echo "Stopping Cowrie honeypot with: $RUN"
$RUN down
