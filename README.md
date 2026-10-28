# nodes

Measurement rounds run from networks other than ours, so a result can be told apart from our own access link.

- `time/` is the public time server probe. The workflow runs one round from a GitHub runner and saves it to `data/time/latest.jsonl`.
- Rounds are triggered by our tick bus, not by a schedule.

Heuremen LLC
