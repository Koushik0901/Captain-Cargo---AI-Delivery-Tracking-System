# AGENTS.md - Captain Cargo AI Agent

This document provides guidelines for AI agents operating in this repository.

## Project Overview

Captain Cargo is a conversational delivery tracking system using FastAPI, Vapi (conversational AI), and Sanity.io. The main entry point is `server.py`.

## Commands

### Running the Server

```bash
uvicorn server:app --reload
```

The server runs on `http://127.0.0.1:8000`. For webhook testing with Vapi, expose locally via `ngrok`.

### Installing Dependencies

```bash
pip install -r requirements.txt
```

### Docker

```bash
docker build -t captain-cargo-agent .
docker run -p 8000:8000 captain-cargo-agent
```

## Code Style Guidelines

### Imports

- Group imports: stdlib, third-party, local modules (in that order)
- Use absolute imports
- Keep imports sorted alphabetically within groups

```python
# Correct
import json
import os
import re
from datetime import datetime

import requests
from fastapi import FastAPI, Request

# Incorrect
import os
import requests
from fastapi import FastAPI
import json
from datetime import datetime
```

### Formatting

- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use blank lines to separate logical sections (2 blank lines between top-level definitions, 1 blank line between methods)
- No trailing whitespace

### Type Hints

- All function parameters and return values MUST have type hints
- Use `Optional[T]` from typing for nullable types, not `T | None`
- Complex generic types should be defined with type aliases

```python
def fetch_from_sanity(tracking_id: str) -> list[dict[str, Any]]:
    ...

def normalize_tracking_id(raw_id: str | None) -> str | None:
    ...
```

### Naming Conventions

- **Variables/functions**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Classes**: `PascalCase`
- **Private methods**: prefix with `_`
- Use descriptive names (no single-letter vars except loop counters)

```python
TRACKING_ID_PATTERN = r"^[A-Z0-9]+$"

def get_delivery_by_tracking(tracking_id: str) -> dict[str, Any]:
    ...
```

### Error Handling

- Use specific exception types (`requests.RequestException`, `ValueError`)
- Never expose sensitive information in error messages
- Always log errors with context before raising
- Use `HTTPException` for API errors with appropriate status codes

```python
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    logger.error(f"Sanity API request failed: {e}")
    raise HTTPException(status_code=503, detail="External service unavailable")
```

### Security

- NEVER use f-strings or string concatenation for SQL/GROQ queries (SQL injection risk)
- Use parameterized queries with proper escaping
- Never log or expose API tokens, passwords, or secrets
- Environment variables for all credentials (`SANITY_PROJECT_ID`, `SANITY_API_TOKEN`, etc.)

```python
# Correct - parameterized query
query = f"*[_type == 'delivery' && trackingNumber == $tracking_id]{{...}}"
params = {"tracking_id": normalized_id}
response = requests.get(url, params={"query": query}, headers=headers)

# Incorrect - SQL injection vulnerable
query = f"*[_type == 'delivery' && trackingNumber == '{normalized_id}']{{...}}"
```

### Logging

- Use a logger instance instead of print statements
- Include request IDs or correlation IDs for traceability
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)

```python
import logging

logger = logging.getLogger(__name__)

def webhook_handler(request: Request):
    logger.info("Received webhook request")
    ...
```

### Async/Await

- Use `async def` for FastAPI endpoints and webhook handlers
- Use `await` for all I/O operations
- Never block in async code

```python
@app.post("/webhook")
async def webhook_handler(request: Request):
    body = await request.json()
    result = await fetch_delivery_async(body["tracking_id"])
    return result
```

### Response Format

- Always return JSON responses with consistent structure
- Include `status` field (`success`, `error`, `not_found`)
- Use `Response` with `media_type="application/json"` for custom responses

### Docstrings

- Use Google-style docstrings for all public functions
- Include Args, Returns, Raises sections

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

### File Organization

- Main application logic in `server.py`
- Keep routes, models, and utilities in separate modules for larger features
- Environment variables in `.env` file (never commit to version control)
