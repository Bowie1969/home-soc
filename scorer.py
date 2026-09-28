#!/usr/bin/env python3
"""SOC scorer — the brain of the tripwire system.

Two live numbers per tracked thing (an IP, a host, a session):
  confidence  how sure we are it's genuinely bad    (0-100; grows with evidence)
  severity    how bad it would be if it IS real     (0-100; worst tripwire seen)

Both decay toward zero when the thing goes quiet, so the score slides smoothly
down the ladder the same way it climbed up. Nothing here touches the network —
tripwires feed it events, and we test it with fake ones.
"""

import math
import time

HALF_LIFE = 300.0  # seconds for evidence to lose half its weight

# Each tripwire: severity = how bad IF real, confidence = how much one hit raises belief.
TRIPWIRES = {
    "honeypot_login":  {"severity": 20, "confidence": 40},
    "fw_drop_spike":   {"severity": 40, "confidence": 10},
    "auth_fail_burst": {"severity": 35, "confidence": 20},
    "new_vlan_host":   {"severity": 50, "confidence": 15},
    "shell_detected":  {"severity": 90, "confidence": 70},
}

# Ladder thresholds (tunable).
CONF_HIGH, SEV_HIGH = 60.0, 70.0
CONF_MED,  SEV_MED  = 20.0, 25.0

# Machine-readable rung levels and human labels.
RUNG_LABELS = {
    0: "LOW",
    1: "MEDIUM",
    2: "WATCH",
    3: "HIGH",
    4: "CRITICAL",
}


def rung_level(confidence, severity):
    """Return the numeric rung level for a (confidence, severity) pair."""
    if confidence >= CONF_HIGH and severity >= SEV_HIGH:
        return 4
    if confidence >= CONF_HIGH:
        return 3
    if severity >= SEV_HIGH:
        return 2
    if confidence >= CONF_MED or severity >= SEV_MED:
        return 1
    return 0


def rung(confidence, severity):
    """Human-readable rung label for a (confidence, severity) pair."""
    return RUNG_LABELS[rung_level(confidence, severity)]


class Scorer:
    def __init__(self):
        self.entities = {}  # name -> {"conf": float, "sev": float, "last": float}

    def _decay(self, e, now):
        delta = max(0.0, now - e["last"])
        factor = math.exp(-delta / HALF_LIFE)
        e["conf"] *= factor
        e["sev"] *= factor
        e["last"] = now

    def hit(self, entity, tripwire, now=None):
        now = time.time() if now is None else now
        e = self.entities.get(entity)
        if e is None:
            e = self.entities[entity] = {"conf": 0.0, "sev": 0.0, "last": now}
        self._decay(e, now)
        t = TRIPWIRES[tripwire]
        e["conf"] = min(100.0, e["conf"] + t["confidence"])
        e["sev"] = max(e["sev"], t["severity"])
        e["last"] = now
        return self.score(entity, now)

    def score(self, entity, now=None):
        now = time.time() if now is None else now
        e = self.entities.get(entity)
        if e is None:
            return 0.0, 0.0, 0, RUNG_LABELS[0]
        self._decay(e, now)
        level = rung_level(e["conf"], e["sev"])
        return round(e["conf"], 1), round(e["sev"], 1), level, RUNG_LABELS[level]


if __name__ == "__main__":
    s = Scorer()
    now = 1_000_000.0

    def show(label, entity="10.10.130.7"):
        conf, sev, level, r = s.score(entity, now)
        print(f"{label:20s} conf={conf:5.1f}  sev={sev:5.1f}  -> {r}")

    print("one entity, fake tripwires only — watch it climb and slide back down:\n")
    show("baseline")
    now += 10
    s.hit("10.10.130.7", "fw_drop_spike", now);   show("+ fw_drop_spike")
    now += 10
    s.hit("10.10.130.7", "auth_fail_burst", now); show("+ auth_fail_burst")
    now += 10
    s.hit("10.10.130.7", "honeypot_login", now);  show("+ honeypot_login")
    now += 10
    s.hit("10.10.130.7", "shell_detected", now);  show("+ shell_detected")
    now += HALF_LIFE
    show("5 min quiet")
    now += HALF_LIFE
    show("10 min quiet")
