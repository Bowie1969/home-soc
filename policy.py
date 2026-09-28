"""SOC policy — map entity type + rung to an action, firing only on transitions.

The policy is intentionally conservative: unknown entity types fail closed
(default "block"), and actions are only emitted when a rung changes so the
sink does not spam.
"""

from scorer import RUNG_LABELS

DEFAULT_ACTIONS = {
    "host": {
        "LOW": "log",
        "MEDIUM": "notify",
        "WATCH": "investigate",
        "HIGH": "quarantine",
        "CRITICAL": "agent",
    },
    "session": {
        "LOW": "log",
        "MEDIUM": "notify",
        "WATCH": "investigate",
        "HIGH": "terminate",
        "CRITICAL": "agent",
    },
}

FAIL_CLOSED = "block"


class Policy:
    def __init__(self, actions=None):
        self.actions = actions if actions is not None else DEFAULT_ACTIONS
        self._last = {}

    def action(self, entity_type, rung_level):
        """Return the action for an entity type at a rung level.

        Unregistered entity types fail closed.
        """
        if entity_type not in self.actions:
            return FAIL_CLOSED
        label = RUNG_LABELS[rung_level]
        return self.actions[entity_type].get(label)

    def transition(self, entity, entity_type, rung_level):
        """Return the action only when the entity's rung changes.

        First-seen entities always count as a transition. Unregistered entity
        types still fail closed on that first transition.
        """
        last = self._last.get(entity)
        self._last[entity] = rung_level
        if last == rung_level:
            return None
        return self.action(entity_type, rung_level)


if __name__ == "__main__":
    p = Policy()
    print("registered host transitions:")
    for level in range(5):
        action = p.transition("10.10.130.7", "host", level)
        print(f"  {RUNG_LABELS[level]:8s} -> {action}")

    print("\nunknown type fails closed:")
    print(f"  {p.transition('weird', 'unknown', 1)}")
