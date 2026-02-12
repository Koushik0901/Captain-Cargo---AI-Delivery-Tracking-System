# 🤖 AGENTS.md

**Guidelines for AI agents working on Captain Cargo**

Hey! 👋 You're here to help build Captain Cargo — the voice agent that actually knows where packages are. Thanks for jumping in!

This doc tells you everything you need to know to write code that fits right in.

---

## 🚢 The Mission

Captain Cargo answers one question really, really well: **"Where's my package?"**

We use:
- **FastAPI** — The webhook handler (talks to Vapi)
- **Vapi** — The voice layer (talks to callers)
- **Sanity.io** — The database (stores delivery data)

Main entry point: `server.py`

---

## 🏃 Getting Started

### Run the Server

```bash
uvicorn server:app --reload
```

Server lives at `http://127.0.0.1:8000`. For webhook testing with Vapi, expose via `ngrok`:

```bash
ngrok http 8000
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Docker

```bash
docker build -t captain-cargo-agent .
docker run -p 8000:8000 captain-cargo-agent
```

---

## 🎨 Code Style Guide

We like our code clean, readable, and consistent. Here's the deal:

### 📦 Imports

Group imports in this order:
1. **stdlib** (Python built-ins)
2. **third-party** (requests, fastapi, etc.)
3. **local modules** (your project's stuff)

```python
# ✅ Good
import json
import os
import re
from datetime import datetime

import requests
from fastapi import FastAPI, Request

# ❌ Bad
import os
import requests
from fastapi import FastAPI
import json
from datetime import datetime
```

Keep imports sorted alphabetically within each group. Use absolute imports.

### 📐 Formatting

- 4 spaces for indentation (no tabs, please)
- Max line length: 100 characters
- Blank lines: 2 between top-level definitions, 1 between methods
- No trailing whitespace — it makes git diffs messy

### 🔤 Type Hints

**ALWAYS use type hints.** They're not optional here.

- Use `Optional[T]` from typing, not `T | None`
- Complex types? Define type aliases

```python
def fetch_from_sanity(tracking_id: str) -> list[dict[str, Any]]:
    ...

def normalize_tracking_id(raw_id: str | None) -> str | None:
    ...
```

### 📛 Naming Conventions

| What | Style | Example |
|------|-------|---------|
| Variables/functions | `snake_case` | `get_delivery_status()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_CACHE_SIZE` |
| Classes | `PascalCase` | `DeliveryCache` |
| Private methods | `_prefix` | `_cleanup_expired()` |

Use descriptive names. `fetch_tracking_data()` is better than `get_data()`. Single-letter vars are only okay for loop counters (`i`, `j`, `k`).

```python
TRACKING_ID_PATTERN = r"^[A-Z0-9]+$"

def get_delivery_by_tracking(tracking_id: str) -> dict[str, Any]:
    ...
```

### ⚠️ Error Handling

- Catch **specific exceptions**, not broad ones
- Never leak secrets in error messages
- Log errors with context before raising
- Use `HTTPException` with appropriate status codes

```python
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    logger.error(f"Sanity API request failed: {e}")
    raise HTTPException(status_code=503, detail="External service unavailable")
```

### 🔒 Security

**THIS IS IMPORTANT.**

- NEVER use f-strings or string concatenation for GROQ queries
- Use parameterized queries
- Never log or expose API tokens, passwords, or secrets
- All credentials go in environment variables

```python
# ✅ Good - parameterized
query = f"*[_type == 'delivery' && trackingNumber == $tracking_id]{{...}}"
params = {"tracking_id": normalized_id}
response = requests.get(url, params={"query": query}, headers=headers)

# ❌ Bad - injection risk
query = f"*[_type == 'delivery' && trackingNumber == '{normalized_id}']{{...}}"
```

### 📝 Logging

Use the logger, not `print()`. Include correlation IDs for tracing.

```python
import logging

logger = logging.getLogger(__name__)

def webhook_handler(request: Request):
    logger.info("Received webhook request", extra={"correlation_id": get_correlation_id()})
    ...
```

Log levels:
- `DEBUG` — Dev notes, internal details
- `INFO` — What happened (general events)
- `WARNING` — Something's off but not broken
- `ERROR` — Something failed

### ⚡ Async/Await

FastAPI is async. Play nice:

- Use `async def` for endpoints and webhook handlers
- Use `await` for ALL I/O operations
- Never block — if you need to, use `run_in_executor()`

```python
@app.post("/webhook")
async def webhook_handler(request: Request):
    body = await request.json()
    result = await fetch_delivery_async(body["tracking_id"])
    return result
```

### 📤 Response Format

Keep responses consistent:

```json
{
  "status": "success" | "error" | "not_found",
  "message": "Human-readable message",
  "delivery_details": { ... }
}
```

### 📖 Docstrings

Use Google-style docstrings for all public functions:

```python
def normalize_tracking_id(raw_id: str) -> str:
    """Normalize tracking ID by removing non-alphanumeric characters.

    Args:
        raw_id: The raw tracking ID from user input.

    Returns:
        Normalized tracking ID in uppercase.

    Raises:
        ValueError: If raw_id is None or empty.
    """
    ...
```

---

## 📁 File Organization

```
captain-cargo/
├── server.py              # Main entry point 🚪
├── models/                # Pydantic models 🧱
│   ├── webhook.py        # Webhook payloads
│   └── delivery.py       # Delivery entities
├── services/              # Business logic 🧠
│   ├── cache.py          # TTL cache
│   ├── sanity_client.py  # Sanity API client
│   └── response_builder.py # Response formatting
├── middleware/            # HTTP middleware 🍵
│   ├── correlation.py   # Correlation IDs
│   └── validation.py    # Request validation
├── utils/                # Utilities 🛠️
│   ├── config.py        # Environment config
│   ├── logger.py        # Structured logging
│   └── normalization.py  # Input normalization
├── endpoints/             # API endpoints 🔌
│   ├── health.py        # /healthz, /readyz
│   └── metrics.py       # /metrics
├── tests/                # 75 tests passing ✅
└── specs/                # Planning docs 🗺️
```

---

## 🧪 Testing

Write tests. Please. For everything.

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/unit/test_cache.py::TestDeliveryCache::test_ttl_expiration -v
```

---

## 🚀 Ready to Code?

1. Read the specs in `specs/001-voice-agent-prod/`
2. Check `tasks.md` for what's being worked on
3. Pick a task and go!
4. Write tests FIRST, make them fail, then implement
5. Run the full test suite before committing

---

## 🙏 Thanks!

You're helping make package tracking less frustrating. One delivery at a time. 📦

Questions? Check the specs, then ask!
