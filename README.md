# home-soc

A small self-hosted SOC, in progress.

- `scorer.py` — keeps a live **confidence + severity** score per entity and maps that pair to a permission ladder.
- `policy.py` — maps entity type + rung to an action, firing only on rung transitions; fails closed on unknown types.
- `sink.py` — delivers alerts via **ntfy** when `NTFY_TOPIC` is set, otherwise dry-run prints.
- `runner.py` — periodic tripwire checks wired through scorer → policy → sink.
- `cowrie.py` — tail Cowrie honeypot JSON logs and emit `honeypot_login`, `auth_fail_burst`, and `shell_detected` hits.
- `honeypot-bait/` — isolated Cowrie container + bait SSH key for scammer engagement. See its README.

Pure Python stdlib for the core; `runner.py` uses `ping` and `sink.py` uses `urllib` for ntfy.

## Run

```bash
python3 scorer.py          # demo the scoring ladder
python3 policy.py          # demo policy transitions
python3 sink.py            # dry-run alert
python3 runner.py --once   # single pass, dry-run by default
NTFY_TOPIC=yourtopic python3 runner.py   # loop and alert for real
```

## Configure

Environment variables:

- `SOC_INTERVAL` — seconds between ticks (default 60)
- `SOC_TARGETS` — override reachability targets as `name=ip;name=ip`
- `SOC_HEX_IP`, `SOC_SG108E_IP` — shortcut defaults for the two built-in targets
- `COWRIE_LOG_PATH` — path to `cowrie.json`; Cowrie tripwires are disabled if unset
- `COWRIE_AUTH_WINDOW` — seconds for the auth-fail burst window (default 60)
- `COWRIE_AUTH_THRESHOLD` — failed logins in that window before a burst hit (default 5)
- `NTFY_TOPIC` — ntfy topic; leave unset for dry-run
- `NTFY_HOST` — self-hosted ntfy server (default `https://ntfy.sh`)
