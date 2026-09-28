# honeypot-bait

Isolated Cowrie SSH honeypot for baiting the `xebaredge.com` scammer.

## Quick start

```bash
./gen-key.sh     # creates bait_key + installs public key into Cowrie
./start.sh       # starts the honeypot on localhost:2222
./watch.py       # live colour tail of events
./stop.sh        # stops the container
```

## What you get

- A throwaway SSH key pair: `bait_key` (private) and `bait_key.pub`.
- Cowrie honeypot running in a rootless Podman container.
- Cowrie accepts **any SSH public key or password** so the bait key just needs to exist, not be pre-registered.
- JSON logs written to `cowrie-logs/cowrie.json`.
- Live viewer with colour-coded events.

## Exposing it to the scammer

**Do not expose this from your home network.** The honeypot runs on `localhost:2222` by design.

Safer options:

1. **Cloud VPS** — copy this `honeypot-bait/` folder to a cheap VPS, install Podman, and run `./start.sh`. Then open TCP/2222 in the cloud firewall.
2. **Existing DO Cowrie host** — point the scammer at the Cowrie you already have running on DigitalOcean; this local setup is for testing/dev.

## Wiring into the SOC

The main `runner.py` can read this Cowrie log directly:

```bash
COWRIE_LOG_PATH=honeypot-bait/cowrie-logs/cowrie.json python3 runner.py --once
```

## Safety notes

- The container is on its own Podman network, not your home LAN.
- Cowrie accepts **any password** by default, so the scammer can log in even if the key doesn't work for them.
- The bait key is throwaway: never reuse it for anything real.
- Wipe `cowrie-data/` and `cowrie-logs/` after the bait is over.
