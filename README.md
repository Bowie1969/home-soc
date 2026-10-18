# home-soc

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Last commit](https://img.shields.io/github/last-commit/Bowie1969/home-soc)](https://github.com/Bowie1969/home-soc)

A small self-hosted SOC that turns raw detection signals into a **confidence × severity** score and escalates responses up a **permission ladder** — fail-closed by default.

## What it is

`home-soc` is a defensive monitoring core written in pure Python (stdlib only, no dependencies). It watches two signal sources — ICMP reachability of lab hosts and a Cowrie SSH honeypot log — scores every observed entity on two axes, and maps the resulting score to escalating automated actions. It is intentionally small: one scorer, one policy table, one alert sink, one runner.

The core idea is that a signal is only useful if you know both *how sure you are* and *how bad it would be*. A high-severity event with low confidence stays low on the ladder; repeated evidence climbs it. Both numbers decay over time, so an entity slides back down the ladder when it goes quiet.

## Highlights

- **Two-axis scoring** — `confidence` (how sure it's bad, grows with evidence) × `severity` (how bad if real, worst tripwire seen), both decaying with a 5-minute half-life.
- **Permission ladder** — `LOW → MEDIUM → WATCH → HIGH → CRITICAL` maps to `log → notify → investigate → quarantine → agent`.
- **Fail-closed policy** — unknown entity types default to `block`; alerts fire only on rung *transitions*, so the sink never spams.
- **Zero dependencies** — the whole core is the Python standard library.
- **Cowrie honeypot integration** — detects successful logins, auth-failure bursts, and first-command shell activity.
- **Safe alerting** — `ntfy` delivery when `NTFY_TOPIC` is set, dry-run printing otherwise, so no secret ever lives in the repo.
- **Optional isolated honeypot** — a rootless Podman/Docker Cowrie container (localhost-only by default) in [`honeypot-bait/`](honeypot-bait/).

## Architecture

```
                       ┌──────────────────────────────┐
                       │           Signals            │
                       │  ICMP reachability checks    │
                       │  Cowrie honeypot JSON log    │
                       └──────────────┬───────────────┘
                                      │ tripwire hits
                                      ▼
        ┌─────────────────────────────────────────────────────────┐
        │                       runner.py                          │
        │        one tick: collect → score → decide → alert        │
        └───────────┬──────────────────┬──────────────┬───────────┘
                    ▼                  ▼              ▼
             ┌────────────┐     ┌─────────────┐  ┌────────────┐
             │  scorer.py  │     │  policy.py  │  │   sink.py  │
             │ confidence  │────▶│  rung →     │─▶│  ntfy /    │
             │ × severity  │     │  action     │  │  dry-run   │
             └────────────┘     └─────────────┘  └────────────┘
```

| Module      | Role                                                                 |
|-------------|----------------------------------------------------------------------|
| `scorer.py` | Live confidence + severity per entity, decay, and the rung ladder.    |
| `policy.py` | Maps entity type + rung to an action; fails closed, transition-only. |
| `sink.py`   | Delivers alerts via ntfy, or dry-run prints when unconfigured.        |
| `runner.py` | Periodic loop wiring reachability + Cowrie hits through the pipeline. |
| `cowrie.py` | Tails Cowrie JSON logs into `honeypot_login`, `auth_fail_burst`, `shell_detected`. |

## Install

No dependencies, no virtualenv needed — clone and run.

```bash
git clone https://github.com/Bowie1969/home-soc.git
cd home-soc
```

Requires Python 3.8+.

## Quickstart

Each module doubles as a self-contained demo:

```bash
python3 scorer.py          # watch an entity climb the ladder and slide back down
python3 policy.py          # show rung → action transitions, and the fail-closed default
python3 sink.py            # dry-run alert (no NTFY_TOPIC set)
python3 runner.py --once   # single pass: ping targets, score, alert (dry-run)
```

To run it for real, point it at an ntfy topic and let it loop:

```bash
NTFY_TOPIC=yourtopic python3 runner.py
```

## Configuration

All settings are environment variables — no config files, no secrets in the repo.

| Variable                  | Purpose                                                        | Default               |
|---------------------------|----------------------------------------------------------------|-----------------------|
| `SOC_INTERVAL`            | Seconds between runner ticks.                                  | `60`                  |
| `SOC_TARGETS`             | Reachability targets as `name=ip;name=ip`.                     | `hEX mgmt`, `SG108E mgmt` |
| `SOC_HEX_IP`              | IP override for the first built-in target.                     | `10.10.130.1`         |
| `SOC_SG108E_IP`           | IP override for the second built-in target.                    | `10.10.130.2`         |
| `COWRIE_LOG_PATH`         | Path to `cowrie.json`; Cowrie tripwires are disabled if unset. | unset                 |
| `COWRIE_AUTH_WINDOW`      | Seconds in the auth-fail burst window.                         | `60`                  |
| `COWRIE_AUTH_THRESHOLD`   | Failed logins in that window before a burst hit.               | `5`                   |
| `NTFY_TOPIC`              | ntfy topic to post alerts to; unset = dry-run.                 | unset                 |
| `NTFY_HOST`               | Self-hosted ntfy server base URL.                              | `https://ntfy.sh`     |

### Optional: honeypot

`honeypot-bait/` provides an isolated Cowrie container that feeds the same scorer. See its [README](honeypot-bait/README.md).

## License

[MIT](LICENSE) © 2026 Will Archer

## Authorized use

This project is for **defensive monitoring of systems and networks you own or are authorized to protect**. The honeypot components are designed to capture unauthorized access attempts against your *own* infrastructure. Do not use this software to target, monitor, or disrupt any system without explicit authorization — unauthorized access to computer systems is illegal in most jurisdictions.
