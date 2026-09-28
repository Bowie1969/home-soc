#!/usr/bin/env python3
"""Live tail of the Cowrie honeypot JSON log.

Prints events as they arrive, colour-coded by type.
"""

import json
import os
import sys
import time

LOG_PATH = os.environ.get("COWRIE_LOG_PATH", "cowrie-logs/cowrie.json")

COLOURS = {
    "cowrie.session.connect": "\033[36m",      # cyan
    "cowrie.login.success": "\033[32m",        # green
    "cowrie.login.failed": "\033[31m",         # red
    "cowrie.command.input": "\033[33m",        # yellow
    "cowrie.session.file_download": "\033[35m", # magenta
    "cowrie.session.closed": "\033[90m",       # grey
}
RESET = "\033[0m"


def tail_file(path):
    """Yield new lines from a file, waiting for more."""
    pos = 0
    while True:
        if not os.path.exists(path):
            time.sleep(0.5)
            continue
        with open(path, "r") as fh:
            fh.seek(pos)
            for line in fh:
                yield line.strip()
            pos = fh.tell()
        time.sleep(0.2)


def render(event):
    etype = event.get("eventid", "unknown")
    colour = COLOURS.get(etype, "")
    ts = event.get("timestamp", event.get("time", "?"))
    src = event.get("src_ip", "?")
    session = event.get("session", "?")[:8]
    username = event.get("username", "")
    password = event.get("password", "")
    command = event.get("input", "")

    parts = [str(ts), f"{session:>8}", f"{src:>16}", etype]
    if username:
        parts.append(f"user={username}")
    if password:
        parts.append(f"pass={password}")
    if command:
        parts.append(f"cmd={command[:80]}")

    line = " | ".join(parts)
    return f"{colour}{line}{RESET}"


def main():
    print(f"Tailing {LOG_PATH}... (Ctrl-C to stop)")
    for raw in tail_file(LOG_PATH):
        if not raw:
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        print(render(event))
        sys.stdout.flush()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
