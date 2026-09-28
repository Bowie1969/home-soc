#!/usr/bin/env bash
# Generate a throwaway SSH key pair for the honeypot bait.
# The public key is copied where Cowrie expects authorized_keys.
set -euo pipefail

cd "$(dirname "$0")"

KEY="bait_key"
if [[ -f "$KEY" ]]; then
    echo "Key already exists: $KEY"
else
    ssh-keygen -t ed25519 -f "$KEY" -N "" -C "bait-key-for-cowrie"
    chmod 600 "$KEY"
    chmod 644 "$KEY.pub"
    echo "Generated: $KEY and $KEY.pub"
fi

echo "Cowrie is configured to accept any SSH public key (auth_publickey_allow_any=true)."
