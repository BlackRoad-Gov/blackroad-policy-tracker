<!-- BlackRoad SEO Enhanced -->

# ulackroad policy tracker

> Part of **[BlackRoad OS](https://blackroad.io)** — Sovereign Computing for Everyone

[![BlackRoad OS](https://img.shields.io/badge/BlackRoad-OS-ff1d6c?style=for-the-badge)](https://blackroad.io)
[![BlackRoad-Gov](https://img.shields.io/badge/Org-BlackRoad-Gov-2979ff?style=for-the-badge)](https://github.com/BlackRoad-Gov)

**ulackroad policy tracker** is part of the **BlackRoad OS** ecosystem — a sovereign, distributed operating system built on edge computing, local AI, and mesh networking by **BlackRoad OS, Inc.**

### BlackRoad Ecosystem
| Org | Focus |
|---|---|
| [BlackRoad OS](https://github.com/BlackRoad-OS) | Core platform |
| [BlackRoad OS, Inc.](https://github.com/BlackRoad-OS-Inc) | Corporate |
| [BlackRoad AI](https://github.com/BlackRoad-AI) | AI/ML |
| [BlackRoad Hardware](https://github.com/BlackRoad-Hardware) | Edge hardware |
| [BlackRoad Security](https://github.com/BlackRoad-Security) | Cybersecurity |
| [BlackRoad Quantum](https://github.com/BlackRoad-Quantum) | Quantum computing |
| [BlackRoad Agents](https://github.com/BlackRoad-Agents) | AI agents |
| [BlackRoad Network](https://github.com/BlackRoad-Network) | Mesh networking |

**Website**: [blackroad.io](https://blackroad.io) | **Chat**: [chat.blackroad.io](https://chat.blackroad.io) | **Search**: [search.blackroad.io](https://search.blackroad.io)

---


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
