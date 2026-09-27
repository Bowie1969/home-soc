# home-soc

A small self-hosted SOC, in progress. The current piece is the scoring brain:
tripwires feed it events, it keeps a live **confidence + severity** score per
entity, and maps that pair to a permission ladder (log → notify → auto-contain →
agent). Pure Python stdlib, no network — tested with fake events.

## Run

```bash
python3 scorer.py
```
