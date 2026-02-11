# Captain Cargo - Conversational Delivery Tracking System

A production-grade voice agent for delivery tracking using FastAPI, Vapi (conversational AI), and Sanity.io.

## Overview

Captain Cargo enables customers to call in and receive accurate delivery status information through a conversational AI interface. The system handles delivery status queries, issue reporting, and graceful degradation during backend outages.

## Features

- **Conversational Interface**: Natural language voice queries for delivery status
- **Production-Grade Reliability**: Circuit breaker, retry logic, and caching
- **Observability**: Health checks, metrics, and structured logging
- **Hallucination-Safe**: Verified backend data only in responses
- **Evaluation Harness**: Transcript replay and accuracy scoring

## Quick Start

### Prerequisites

- Python 3.11+
- Sanity CMS account

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd captain-cargo

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your Sanity credentials
```

### Running the Server

```bash
# Development
uvicorn server:app --reload

# Production
python server.py
```

The server runs on `http://127.0.0.1:8000`.

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|------------|---------|----------|
| `SANITY_PROJECT_ID` | Sanity CMS project ID | - | Yes |
| `SANITY_DATASET` | Sanity dataset name | `production` | No |
| `SANITY_API_TOKEN` | Sanity API read token | - | Yes |
| `CACHE_TTL` | Cache TTL in seconds | `60` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `RATE_LIMIT` | Requests per minute | `100` | No |

### Sanity Schema Requirements

Your Sanity dataset should include a `delivery` document type with:

```groq
*[_type == "delivery"]{
  trackingNumber,
  status,
  customerName,
  customerPhone,
  estimatedDelivery,
  issueMessage
}
```

## API Endpoints

### Health Checks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthz` | GET | Kubernetes liveness probe |
| `/readyz` | GET | Kubernetes readiness probe with dependency status |
| `/metrics` | GET | JSON metrics for monitoring |

### Webhook

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook` | POST | Vapi webhook handler for delivery queries |

### Webhook Payload Format

```json
{
  "message": {
    "content": "What's the status of my package?",
    "toolCalls": [
      {
        "function": {
          "name": "track_delivery",
          "arguments": "{\"trackingId\": \"TRK123456789\"}"
        }
      }
    ]
  }
}
```

## Architecture

```
                        VOICE CALLER
                              |
                              v
                      +-------------+
                      |   Vapi     |  (speech-to-text, text-to-speech)
                      |   Platform  |
                      +------+------+
                             |
                             | HTTPS POST /webhook
                             v
                     +----------------+
                     |   FastAPI     |  (webhook handler)
                     |   Server      |
                     +------+-------+
                            |
          +------------------+------------------+
          |                  |                  |
          v                  v                  v
   +------------+     +------------+     +------------+
   |    Cache   |     |  Metrics  |     |   Logger   |
   | TTL 60s   |     |            |     |            |
   +------+-----+     +------+-----+     +------+-----+
          |                  |                  |
          +------------------+------------------+
                            |
                            v
                    +----------------+
                    |    Sanity     |
                    |    CMS API    |
                    +----------------+
```

## Project Structure

```
captain-cargo/
├── server.py                 # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── AGENTS.md               # AI agent guidelines
├── README.md               # This file
├── specs/                  # Feature specifications
│   └── 001-voice-agent-prod/
│       ├── spec.md         # Feature specification
│       ├── plan.md         # Technical plan
│       ├── tasks.md        # Task breakdown
│       └── checklists/     # Quality checklists
├── models/                  # Pydantic models
│   ├── webhook.py          # Webhook payload models
│   └── delivery.py         # Delivery entity models
├── services/                # Business logic
│   ├── cache.py            # TTL cache with stats
│   ├── sanity_client.py    # Sanity CMS client with retry/circuit breaker
│   └── response_builder.py  # Hallucination-safe response builder
├── middleware/              # HTTP middleware
│   ├── correlation.py      # Correlation ID propagation
│   └── validation.py       # Request validation
├── utils/                   # Utilities
│   ├── config.py           # Environment validation
│   ├── logger.py           # Structured JSON logging
│   └── normalization.py    # Tracking ID normalization
├── endpoints/               # API endpoints
│   ├── health.py           # Health check endpoints
│   └── metrics.py          # Metrics endpoint
├── scripts/                 # Utility scripts
│   └── eval_replay.py      # Evaluation harness
└── tests/                   # Test suite
    ├── unit/               # Unit tests
    ├── contract/           # Contract tests
    └── integration/        # Integration tests
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=. tests/

# Run specific test file
pytest tests/unit/test_normalization.py -v

# Run specific test
pytest tests/unit/test_cache.py::TestDeliveryCache::test_ttl_expiration -v
```

### Test Categories

- **Unit Tests**: Test individual functions and classes
- **Contract Tests**: Test Pydantic model validation
- **Integration Tests**: Test full request/response cycles

### Test Results

```
======================== 75 passed, 1 warning in 3.67s ========================
```

## Production Deployment

### Docker

```bash
# Build image
docker build -t captain-cargo-agent .

# Run container
docker run -p 8000:8000 \
  -e SANITY_PROJECT_ID=xxx \
  -e SANITY_DATASET=production \
  -e SANITY_API_TOKEN=xxx \
  captain-cargo-agent
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: captain-cargo
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: captain-cargo
        image: captain-cargo-agent
        ports:
        - containerPort: 8000
        env:
        - name: SANITY_PROJECT_ID
          valueFrom:
            secretKeyRef:
              name: sanity-credentials
              key: project-id
        - name: SANITY_API_TOKEN
          valueFrom:
            secretKeyRef:
              name: sanity-credentials
              key: api-token
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8000
```

## Evaluation Harness

Replay voice interactions and score accuracy:

```bash
python scripts/eval_replay.py \
  --input eval/cases.jsonl \
  --server http://localhost:8000 \
  --report eval/report.md \
  --format markdown
```

### Cases File Format (JSONL)

```jsonl
{"timestamp":"2024-01-15T10:00:00Z","correlation_id":"abc123","transcript":"Where is my package?","tool_calls":[{"function":{"name":"track_delivery","arguments":{"tracking_id":"ABC123"}}}],"expected_status":"success"}
{"timestamp":"2024-01-15T10:05:00Z","correlation_id":"def456","transcript":"Check status for XYZ789","tool_calls":[{"function":{"name":"track_delivery","arguments":{"tracking_id":"XYZ789"}}}],"expected_status":"not_found"}
```

## Key Features

### Reliability Patterns

- **Circuit Breaker**: Prevents cascade failures during Sanity outages
- **Retry Logic**: Exponential backoff (3 attempts, 100ms-400ms)
- **TTL Cache**: 60-second cache with LRU eviction
- **Timeout Enforcement**: 800ms P95 latency target

### Observability

- **Correlation IDs**: End-to-end request tracing
- **Structured Logging**: JSON logs with correlation IDs
- **Metrics**: Request counts, cache hits/misses, latency percentiles
- **Health Checks**: Liveness, readiness, and dependency status

### Safety

- **Hallucination-Safe**: Responses contain only verified backend data
- **Input Validation**: Pydantic-validated webhook payloads
- **Error Handling**: Graceful degradation with fallback responses

## Contributing

See [AGENTS.md](AGENTS.md) for AI agent guidelines.

## License

MIT
