---
description: Avoid hardcoding deprecated model versions; enforce centralized client creation, supported Gemini 3.x models, and transient retry handling.
---
# Dynamic API Resolution & Model Invariants

1. **Centralized Client & Model Management:**
   - Never hand-roll custom `genai.Client` instances or ad-hoc API call loops.
   - Always route Gemini API calls through `pipeline/vision_adjudication_common.py` using `make_client()` and `adjudicate_with_retry()`.

2. **Model Version Invariant:**
   - **Never call `gemini-2.x` or `gemini-2.5-flash`** (permanently deprecated / 404 since 2026-08-05).
   - The active primary model is `gemini-3.6-flash`, with `gemini-3.5-flash` as the secondary fallback.
   - If querying models dynamically, always filter for active supported generation methods and avoid hardcoded legacy versions.

3. **Transient Error Handling (503 / 429):**
   - All live API calls must be wrapped in exponential backoff retry loops catching transient `503 UNAVAILABLE` (spikes in demand) and `429 RESOURCE_EXHAUSTED` errors before failing.
