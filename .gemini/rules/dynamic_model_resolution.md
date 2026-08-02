---
description: Avoid hardcoding SDK model versions; dynamically query APIs to resolve the active/supported model instead of downgrading frameworks.
---
# Dynamic API Resolution Over Hardcoding

Never hardcode specific LLM version strings (like `gemini-3.5-flash` or `gemini-2.5-flash`) when building pipelines. Instead, dynamically query the API for available models, filter for the desired model family (like `flash`), and programmatically select the active/supported model. Always use the most modern, maintained SDK available rather than falling back to older frameworks.

**Implementation Pattern:**
```python
from google import genai
import os

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
models = [m for m in client.models.list() if 'generateContent' in m.supported_generation_methods]
target_model = models[0].name if models else 'gemini-1.5-pro'
```
