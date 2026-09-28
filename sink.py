"""SOC sink — deliver alerts.

Uses ntfy when NTFY_TOPIC is set, otherwise prints a dry-run line so the
secret topic name never has to live in the repo.
"""

import os
import urllib.request

NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
NTFY_HOST = os.environ.get("NTFY_HOST", "https://ntfy.sh")

PRIORITY = {
    "low": 1,
    "medium": 2,
    "watch": 3,
    "high": 4,
    "critical": 5,
}


def send(title, message, tags=None, priority=None):
    """Post a message to the configured ntfy topic, or dry-run if unset."""
    topic = NTFY_TOPIC
    if not topic:
        print(f"[sink dry-run] {title}: {message}")
        return True

    url = f"{NTFY_HOST}/{topic}"
    req = urllib.request.Request(url, data=message.encode(), method="POST")
    req.add_header("Title", title)
    if tags:
        req.add_header("Tags", ",".join(tags))
    if priority:
        req.add_header("Priority", str(priority))
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as exc:
        print(f"[sink error] {exc}")
        return False


def alert(entity, entity_type, action, conf, sev, label):
    """Send a SOC alert for an entity transition."""
    title = f"SOC {action.upper()}: {entity}"
    body = f"{entity_type} {entity} is {label} (conf={conf}, sev={sev})"
    tags = [action, label.lower()]
    priority = PRIORITY.get(label.lower(), 3)
    return send(title, body, tags=tags, priority=priority)


if __name__ == "__main__":
    send("SOC test", "Dry-run alert from home-soc sink.py")
