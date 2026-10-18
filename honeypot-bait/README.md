# honeypot-bait

Isolated Cowrie SSH honeypot for capturing and fingerprinting unauthorized access attempts against infrastructure you control.

## Quick start

```bash
./gen-key.sh     # creates a throwaway bait key + installs the public key into Cowrie
./start.sh       # starts the honeypot on localhost:2222
./watch.py       # live colour tail of events
./stop.sh        # stops the container
```

## What you get

- A throwaway SSH key pair: `bait_key` (private) and `bait_key.pub` — both gitignored.
- Cowrie running in a rootless Podman/Docker container on an isolated network.
- Cowrie accepts any SSH public key or password, so the key only needs to exist.
- JSON logs written to `cowrie-logs/cowrie.json`.
- A live colour-coded event viewer.

## Deploying it

The container binds to `localhost:2222` by design and sits on its own network — it cannot reach host services.

To capture real internet traffic:

1. **Cloud VPS** — copy this `honeypot-bait/` folder to a VPS, install Podman, run `./start.sh`, and open TCP/2222 in the cloud firewall only.
2. **Existing honeypot host** — point `runner.py` at a Cowrie log you already run elsewhere; this local setup is for testing/dev.

Do **not** forward this from your home network to the internet.

## Wiring into the SOC

The main `runner.py` reads this Cowrie log directly:

```bash
COWRIE_LOG_PATH=honeypot-bait/cowrie-logs/cowrie.json python3 runner.py --once
```

## Safety notes

- The container runs on its own Podman network, not your LAN.
- Cowrie accepts any password by default, so unauthorised logins still land in a sandbox.
- The bait key is throwaway: never reuse it for anything real.
- Wipe `cowrie-data/` and `cowrie-logs/` after the engagement is over.
