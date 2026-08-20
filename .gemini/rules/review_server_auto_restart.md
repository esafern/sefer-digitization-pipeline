---
description: Always automatically restart the review server process whenever review_server.py or review_frontend/ assets are modified.
---
# Review Server Auto-Restart Rule

1. **Automatic Restart on Code/Asset Edits:**
   - Whenever changes are made to `pipeline/review_server.py` or any file in `review_frontend/` (`app.js`, `app.css`, `index.html`), **always automatically restart the review server background process** (`python3 pipeline/review_server.py` on port 8420).
   - Do not ask for user confirmation or wait to be prompted—restart immediately after making the file modifications.

2. **Process Restart Discipline:**
   - Check and kill any existing listener on port 8420 (`lsof -i :8420` -> `kill <PID>`).
   - Relaunch the process in the background (`python3 pipeline/review_server.py`).
   - Verify port 8420 is listening cleanly before completing the edit step.
