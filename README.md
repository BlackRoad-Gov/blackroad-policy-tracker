# blackroad-policy-tracker

> Government policy and legislation tracker

Part of the [BlackRoad OS](https://blackroad.io) ecosystem — [BlackRoad-Gov](https://github.com/BlackRoad-Gov)

---

# blackroad-policy-tracker

Government policy and legislation tracker with full-text search.

## Features
- Track laws, regulations, ordinances, and executive orders
- Full-text search using SQLite FTS5
- Amendment tracking with section-level diffs
- Public comment system with sentiment analysis
- Policy lifecycle management (draft → proposed → enacted → repealed)
- Export detailed policy reports

## Policy Lifecycle
`draft` → `proposed` → `enacted` → `amended` / `repealed`

## Usage
```bash
python policy_tracker.py list
python policy_tracker.py search "environmental"
python policy_tracker.py stats
python policy_tracker.py report <policy_id>
```

## Run Tests
```bash
pip install pytest
pytest tests/ -v
```
