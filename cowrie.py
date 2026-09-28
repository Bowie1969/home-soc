"""Cowrie honeypot log tailer — turn Cowrie JSON events into scorer hits.

Reads a local Cowrie JSON log and yields tripwire hits for:
  - honeypot_login   on successful login
  - auth_fail_burst  when failures from one IP exceed the threshold/window
  - shell_detected   on the first command in a session
"""

import json
import os
import time

EVENT_LOGIN_SUCCESS = "cowrie.login.success"
EVENT_LOGIN_FAILED = "cowrie.login.failed"
EVENT_COMMAND = "cowrie.command.input"


class CowrieTailer:
    def __init__(self, path, state_path=None):
        self.path = path
        self.state_path = state_path
        self._pos = 0
        self._failures = {}
        self._shelled = set()
        self._auth_window = int(os.environ.get("COWRIE_AUTH_WINDOW", "60"))
        self._auth_threshold = int(os.environ.get("COWRIE_AUTH_THRESHOLD", "5"))

    def _read_new_lines(self):
        if not self.path or not os.path.exists(self.path):
            return
        with open(self.path, "r") as fh:
            fh.seek(self._pos)
            for line in fh:
                line = line.strip()
                if line:
                    yield line
            self._pos = fh.tell()

    def _now(self, event):
        return event.get("time", time.time())

    def _src_ip(self, event):
        return event.get("src_ip")

    def _trim_failures(self, ip, now):
        cutoff = now - self._auth_window
        self._failures[ip] = [t for t in self._failures.get(ip, []) if t > cutoff]

    def poll(self):
        """Return a list of (tripwire, entity, timestamp) hits since last poll."""
        hits = []
        for raw in self._read_new_lines():
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue

            etype = event.get("eventid")
            ip = self._src_ip(event)
            now = self._now(event)
            if not etype or not ip:
                continue

            if etype == EVENT_LOGIN_SUCCESS:
                hits.append(("honeypot_login", ip, now))

            elif etype == EVENT_LOGIN_FAILED:
                self._trim_failures(ip, now)
                self._failures.setdefault(ip, []).append(now)
                if len(self._failures[ip]) >= self._auth_threshold:
                    hits.append(("auth_fail_burst", ip, now))

            elif etype == EVENT_COMMAND:
                session = event.get("session")
                if session and session not in self._shelled:
                    self._shelled.add(session)
                    hits.append(("shell_detected", ip, now))

        return hits


if __name__ == "__main__":
    import tempfile

    sample = [
        json.dumps({"eventid": EVENT_LOGIN_FAILED, "src_ip": "192.0.2.1", "time": time.time()}),
        json.dumps({"eventid": EVENT_LOGIN_SUCCESS, "src_ip": "192.0.2.1", "time": time.time()}),
        json.dumps({"eventid": EVENT_COMMAND, "src_ip": "192.0.2.1", "session": "a1", "time": time.time()}),
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fh:
        for line in sample:
            fh.write(line + "\n")
        path = fh.name

    try:
        os.environ["COWRIE_AUTH_THRESHOLD"] = "1"
        tailer = CowrieTailer(path)
        hits = tailer.poll()
        for tripwire, entity, ts in hits:
            print(f"{tripwire:18s} {entity} @ {ts}")
    finally:
        os.unlink(path)
