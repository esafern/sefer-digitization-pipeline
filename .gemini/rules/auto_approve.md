---
description: Auto-approve non-destructive python3, pytest, and review server commands to execute seamlessly without interrupting workflow.
---

# Command Auto-Approval Directives

1. **Python Execution & Testing**:
   - Auto-approve all non-destructive `python3` and `pytest` execution commands, including any command starting with `PYTHONPATH=pipeline` (e.g. `PYTHONPATH=pipeline python3 ...`, `PYTHONPATH=pipeline python3 -c '...'`, `pytest tests/ -v`).
   - Run tests and verification commands silently in the background or synchronously without requesting manual user approval.

2. **Server Management**:
   - Auto-approve process management, `lsof`, and port cleanup commands required for review server auto-restart (e.g. `lsof -t -i :8420 | xargs kill -9 2>/dev/null; python3 pipeline/review_server.py`).
