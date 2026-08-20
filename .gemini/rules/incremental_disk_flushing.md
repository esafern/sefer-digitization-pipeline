---
description: Mandatory standing rule requiring all pipeline, API, and data-processing scripts to flush work to disk incrementally after every item.
---
# Mandatory Incremental Disk Flushing Rule

1. **Never Buffer Entire Batch Output in Memory**:
   - All scripts that perform batch processing, API calls (Gemini, DocAI, Dicta, Kraken), dataset generation, or LLM adjudication **MUST** write and flush their output incrementally to disk after processing each individual item (klal, page, word, or candidate).

2. **File & Database Discipline**:
   - For file-based output (`.txt`, `.jsonl`, `.json`), open in append/write mode per item or write and call `f.flush()` / `os.fsync(f.fileno())` immediately after each item completes.
   - For SQLite databases (e.g. `adjudication_cache.db`), issue `conn.commit()` after each transaction.

3. **Rationale**:
   - Cloud API calls, 503 service unavailability, 429 rate limits, network timeouts, and token exhaustion occur frequently in production.
   - Incremental flushing ensures that if a script is interrupted, killed, or rate-limited, **zero progress is lost** and the script can resume from the last completed item seamlessly.
