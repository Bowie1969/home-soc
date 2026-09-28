"""SOC runner — periodic tripwire checks wired through scorer -> policy -> sink."""

import argparse
import os
import subprocess
import sys
import time

from scorer import Scorer
from policy import Policy
from sink import alert

INTERVAL = int(os.environ.get("SOC_INTERVAL", "60"))

# Default reachability targets. Override with SOC_TARGETS as
# "name=ip;name=ip" or edit here for your lab.
DEFAULT_TARGETS = {
    "hEX mgmt": os.environ.get("SOC_HEX_IP", "10.10.130.1"),
    "SG108E mgmt": os.environ.get("SOC_SG108E_IP", "10.10.130.2"),
}


def _parse_targets(raw):
    if not raw:
        return DEFAULT_TARGETS
    out = {}
    for pair in raw.split(";"):
        name, ip = pair.split("=", 1)
        out[name.strip()] = ip.strip()
    return out


def ping(host, count=1, timeout=3):
    """Return True if host answers ICMP echo."""
    cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_reachability(scorer, targets):
    """Ping each target; a miss registers a fw_drop_spike hit."""
    for name, ip in targets.items():
        if not ping(ip):
            scorer.hit(name, "fw_drop_spike")


def tick(scorer, policy, targets):
    """One pass: collect tripwires, score, check policy, alert on transitions."""
    check_reachability(scorer, targets)
    now = time.time()
    for entity in list(scorer.entities.keys()):
        conf, sev, level, label = scorer.score(entity, now)
        action = policy.transition(entity, "host", level)
        if action:
            alert(entity, "host", action, conf, sev, label)


def main():
    parser = argparse.ArgumentParser(description="Home SOC runner")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single tick and exit instead of looping.",
    )
    args = parser.parse_args()

    targets = _parse_targets(os.environ.get("SOC_TARGETS"))
    scorer = Scorer()
    policy = Policy()

    print(f"SOC runner started; interval={INTERVAL}s")
    print(f"Targets: {', '.join(f'{n} ({ip})' for n, ip in targets.items())}")

    if args.once:
        tick(scorer, policy, targets)
        return

    try:
        while True:
            tick(scorer, policy, targets)
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nSOC runner stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
