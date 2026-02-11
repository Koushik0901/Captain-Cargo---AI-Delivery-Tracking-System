# Implementation Plan: Production-Grade Voice Agent

**Branch**: `001-voice-agent-prod` | **Date**: 2026-02-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-voice-agent-prod/spec.md`

## Summary

Transform the Vapi-integrated delivery tracking voice agent from prototype to production-grade by implementing deterministic tool contracts, resilience patterns, observability, and deploy hardening. The system will handle delivery status inquiries with sub-second latency, graceful degradation during failures, and full auditability for quality evaluation.

Primary technical approach:
- Pydantic models for strict webhook payload validation
- TTL cache with deterministic fallbacks for resilience
- Structured logging with correlation IDs for observability
- JSONL-based evaluation harness for transcript replay

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Pydantic v2, tenacity (retries), prometheus-client
**Storage**: Sanity.io CMS (external), in-memory cache (LRU with TTL)
**Testing**: pytest, pytest-asyncio, httpx for async tests
**Target Platform**: Linux container (AWS App Runner)
**Project Type**: Single FastAPI backend service
**Performance Goals**: <800ms P95 latency, <1% error rate, 60% cache hit ratio
**Constraints**: Vapi 5-second webhook timeout, read-only Sanity access
**Scale/Scope**: 50 concurrent calls, single-node deployment initially

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle I - Deterministic Tool Contracts**:
- [x] Tool contracts will use Pydantic schemas for all Vapi payloads
- [x] Input validation with descriptive errors (422 responses)
- [x] Output schemas define structured response formats with status indicators

**Principle II - Reliability**:
- [x] Retry with exponential backoff (tenacity library)
- [x] Configurable timeouts (500ms for Sanity queries)
- [x] Circuit breaker pattern for datastore outages
- [x] Graceful fallback responses documented

**Principle III - Latency Discipline**:
- [x] In-memory cache with 60s TTL
- [x] Time budgets: webhook processing ≤ 500ms
- [x] Degradation strategy: cached or fallback on slow upstream

**Principle IV - Hallucination Control**:
- [x] Response builder derives text from verified tool outputs only
- [x] Fallback responses clearly state "information unavailable"
- [x] No speculative information in agent responses

**Principle V - Observability**:
- [x] Correlation ID generation and propagation
- [x] Structured JSON logging with appropriate levels
- [x] Prometheus metrics endpoint
- [x] Health endpoints (/healthz, /readyz)

**Principle VI - Evaluation Harness**:
- [x] JSONL transcript recording
- [x] Replay capability for past interactions
- [x] Scoring: accuracy, tool success rate, latency percentiles

**Principle VII - Deploy Hardening**:
- [x] Environment variable validation at startup
- [x] Health checks for Kubernetes probes
- [x] Graceful shutdown handling

**Constitution Validation Gates**:

Before each milestone, verify:
- M1: Principles I, IV satisfied (tool contracts, hallucination control)
- M2: Principles II, III satisfied (reliability, latency discipline)
- M3: Principle V satisfied (observability)
- M4: Principles V, VII satisfied (observability, deploy hardening)

Record gate pass/fail in PR description before code review.

## Project Structure

### Documentation (this feature)

```text
specs/001-voice-agent-prod/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (N/A - no unknowns)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
.
├── server.py            # Main FastAPI application (modified)
├── requirements.txt     # Dependencies (modified)
├── tests/
│   ├── contract/        # Schema validation tests
│   ├── integration/     # End-to-end tests
│   └── unit/           # Unit tests
├── scripts/
│   ├── eval_replay.py   # Evaluation harness
│   └── health_check.py  # Health verification
├── .env.example         # Environment template (new)
└── docker-compose.yml   # Local dev with mock (new)
```

**Structure Decision**: Single FastAPI service at repository root. Tests organized by type under `tests/`. Scripts for operations under `scripts/`.

---

# Milestone 1: Tool Contract Hardening + State Handling

**Timeline**: Week 1

## Rationale

Establishes the foundation for reliable voice agent operation. Strict Pydantic schemas prevent malformed data from causing errors, while normalization ensures consistent tracking ID handling. Basic conversation state logic guides the agent through the natural flow from need → confirm → fetch → report → fallback.

## Tasks

### M1.1: Add Pydantic dependencies and models

- [ ] Add `pydantic>=2.0` to requirements.txt
- [ ] Create `models/webhook.py` with Pydantic models for:
  - Vapi webhook payload (ToolCallRequest, FunctionCall, etc.)
  - Tool response structures (DeliveryStatus, ErrorResponse)
  - Sanity query response models

### M1.2: Implement tracking ID normalization

- [ ] Create `utils/normalization.py` with:
  - `normalize_tracking_id(raw_id: str) -> str`
  - Validation: alphanumeric only, uppercase, 6-32 chars
  - Raises `ValueError` for invalid formats

### M1.3: Add webhook payload validation

- [ ] Create `middleware/validation.py`:
  - Middleware to validate incoming webhook payloads
  - Returns 422 with descriptive error on validation failure
  - Logs validation errors with correlation ID

### M1.4: Implement response builder

- [ ] Create `services/response_builder.py`:
  - `build_success_response(delivery: Delivery) -> dict`
  - `build_not_found_response(tracking_id: str) -> dict`
  - `build_error_response(message: str) -> dict`
  - All responses include `status` field and human-readable `message`

### M1.5: Add correlation ID propagation

- [ ] Create `middleware/correlation.py`:
  - Generate UUID correlation ID for each request
  - Store in context variable (contextvars)
  - Add to all log entries
  - Include in all response headers

## Acceptance Tests

- [ ] Invalid webhook payloads return 422 with error details
- [ ] Tracking IDs with spaces/special chars normalize correctly
- [ ] Valid tracking IDs pass validation (no false positives)
- [ ] All responses include correlation ID in headers and logs
- [ ] Response builder produces consistent output format

## Estimated File Changes

| File | Change |
|------|--------|
| `requirements.txt` | Add pydantic |
| `models/__init__.py` | Create (model exports) |
| `models/webhook.py` | Create (Pydantic schemas) |
| `models/delivery.py` | Create (Delivery entity) |
| `utils/normalization.py` | Create (tracking ID logic) |
| `middleware/validation.py` | Create (webhook validation) |
| `middleware/correlation.py` | Create (correlation IDs) |
| `services/response_builder.py` | Create (response factories) |
| `tests/contract/test_schemas.py` | Create (schema tests) |
| `tests/unit/test_normalization.py` | Create (unit tests) |

## Done Means

- [ ] All incoming webhook payloads validated against Pydantic schemas
- [ ] Invalid payloads return 422 with descriptive error (no server exceptions)
- [ ] Schema violations logged with correlation ID for debugging
- [ ] Tracking ID normalization handles all edge cases (spaces, lowercase, special chars)
- [ ] Response builder produces consistent structure for success/error/not-found
- [ ] Every request has unique correlation ID propagated through logs

---

# Milestone 2: Latency + Resilience

**Timeline**: Week 2

## Rationale

Production voice agents cannot afford extended delays or failures. Caching reduces latency for repeated lookups. Retry logic handles transient Sanity CMS failures. Circuit breaker prevents cascade failures during outages. Deterministic fallbacks ensure users always get a response, even when backends are unavailable.

## Tasks

### M2.1: Implement TTL cache layer

- [ ] Create `services/cache.py`:
  - LRU cache with configurable TTL (default 60s)
  - `get(key: str) -> DeliveryStatus | None`
  - `set(key: str, value: DeliveryStatus, ttl: int = 60)`
  - `invalidate(key: str)`
  - Cache statistics: hits, misses, size

### M2.2: Add retry logic with backoff

- [ ] Create `services/sanity_client.py`:
  - Wrap `requests.get` with tenacity retry
  - Exponential backoff: 100ms → 200ms → 400ms
  - Max 3 attempts before raising exception
  - Timeout per request: 5s total budget

### M2.3: Implement circuit breaker

- [ ] Add circuit breaker pattern to `services/sanity_client.py`:
  - Open after 5 consecutive failures
  - Half-open: allow 1 probe after 30s
  - Closed: normal operation
  - State transitions logged with correlation ID

### M2.4: Add timeout enforcement

- [ ] Create `middleware/timeout.py`:
  - Enforce 500ms timeout on webhook processing
  - If exceeded, return cached data or fallback
  - Log timeout events with correlation ID

### M2.5: Implement deterministic fallbacks

- [ ] Enhance `services/response_builder.py`:
  - `build_cached_fallback(cached_data: dict, age: int) -> dict`
  - `build_unavailable_fallback() -> dict`
  - Both include `source: "cache"` or `source: "fallback"` indicator
  - Human-readable messages: "I have cached information from [time]"

## Acceptance Tests

- [ ] Sanity CMS retry succeeds for 95% of transient failures (tested with simulated failures)
- [ ] Circuit breaker opens after 5 consecutive failures and resets after 30 seconds
- [ ] Cache hit returns data within 50ms
- [ ] Cache TTL expires after 60s (configurable)
- [ ] Timeout enforces 500ms maximum per upstream request
- [ ] Graceful fallback returns cached or "try later" message without hanging

## Estimated File Changes

| File | Change |
|------|--------|
| `services/cache.py` | Create (TTL cache) |
| `services/sanity_client.py` | Create (retry + circuit breaker) |
| `middleware/timeout.py` | Create (timeout enforcement) |
| `services/response_builder.py` | Modify (add fallback methods) |
| `server.py` | Modify (integrate cache/client) |
| `tests/integration/test_cache.py` | Create (cache tests) |
| `tests/integration/test_resilience.py` | Create (retry + circuit breaker tests) |

## Done Means

- [ ] Cached status queries complete in under 500ms P50, 800ms P95
- [ ] Cache hit rate exceeds 60% during steady-state operation
- [ ] Timeout enforces 5-second maximum per upstream request
- [ ] Circuit breaker opens after 5 consecutive failures and resets after 30 seconds
- [ ] Graceful fallback returns cached or "try later" message without hanging
- [ ] Retry succeeds for 95% of transient Sanity CMS failures

---

# Milestone 3: Observability + Evaluation

**Timeline**: Week 3

## Rationale

Operators need visibility into system behavior during live calls. Structured logs with correlation IDs enable post-hoc debugging. Metrics provide real-time health visibility. Evaluation harness enables quality assurance through replay and scoring, catching regressions before they affect users.

## Tasks

### M3.1: Implement structured logging

- [ ] Create `utils/logger.py`:
  - JSON formatter for all log output
  - Log levels: DEBUG (request details), INFO (operations), WARNING (degradations), ERROR (failures)
  - Required fields: `timestamp`, `level`, `correlation_id`, `event`, `latency_ms`
  - No sensitive data (tokens, tracking IDs masked)

### M3.2: Add metrics endpoint

- [ ] Create `endpoints/metrics.py`:
  - Prometheus-compatible /metrics endpoint
  - Counters: `requests_total`, `errors_total`, `cache_hits_total`, `cache_misses_total`
  - Histograms: `request_latency_seconds`, `sanity_latency_seconds`
  - Gauge: `circuit_breaker_state`

### M3.3: Implement health endpoints

- [ ] Create `endpoints/health.py`:
  - `/healthz`: liveness check (process running)
  - `/readyz`: readiness check (circuit breaker closed, Sanity accessible)
  - Both respond within 50ms
  - Include dependency status in /readyz response

### M3.4: Build evaluation harness

- [ ] Create `scripts/eval_replay.py`:
  - Read JSONL transcripts from `var/log/transcripts/`
  - Replay tool calls against current server
  - Capture: response, latency, success/failure
  - Output: accuracy score, tool success rate, latency percentiles

### M3.5: Add transcript recording

- [ ] Create `middleware/recording.py`:
  - Log each voice interaction to JSONL
  - Fields: timestamp, correlation_id, transcript, tool_calls, response
  - Separate file per day: `transcripts-YYYY-MM-DD.jsonl`
  - Archival after 30 days (configurable)

## Acceptance Tests

- [ ] Every request logged with correlation ID, latency, and status
- [ ] Health endpoint responds within 50ms
- [ ] Metrics exposed in Prometheus-compatible format
- [ ] All voice interactions recorded with transcript and tool calls
- [ ] Replay tool can reproduce any past interaction deterministically
- [ ] Automated scoring identifies hallucination and latency regressions

## Estimated File Changes

| File | Change |
|------|--------|
| `utils/logger.py` | Create (structured logging) |
| `endpoints/metrics.py` | Create (Prometheus metrics) |
| `endpoints/health.py` | Create (health checks) |
| `middleware/recording.py` | Create (transcript recording) |
| `scripts/eval_replay.py` | Create (evaluation harness) |
| `scripts/archive_transcripts.py` | Create (optional archival) |
| `server.py` | Modify (register endpoints) |
| `tests/integration/test_observability.py` | Create (log + metrics tests) |

## Done Means

- [ ] Every request logged with correlation ID, latency, and status
- [ ] Health endpoint responds within 50ms
- [ ] Metrics exposed in Prometheus-compatible format
- [ ] All voice interactions recorded with transcript and tool calls
- [ ] Replay tool can reproduce any past interaction deterministically
- [ ] Automated scoring identifies hallucination and latency regressions

---

# Milestone 4: Deploy Hardening

**Timeline**: Week 4

## Rationale

Production deployments must start correctly, validate their configuration, and shut down gracefully. Environment variable validation prevents misconfiguration issues at runtime. Rate limiting protects against abuse. Documentation ensures operators can deploy and operate the system confidently.

## Tasks

### M4.1: Add environment validation

- [ ] Create `utils/config.py`:
  - Validate `SANITY_PROJECT_ID`, `SANITY_DATASET`, `SANITY_API_TOKEN` at startup
  - Fail fast with descriptive error if missing
  - Optional: validate API token format

### M4.2: Implement rate limiting

- [ ] Create `middleware/ratelimit.py`:
  - Token bucket or sliding window counter
  - Limit: 100 requests per minute per correlation source
  - Return 429 with "try again later" message
  - Log rate limit events

### M4.3: Add graceful shutdown

- [ ] Modify `server.py`:
  - Signal handlers for SIGTERM, SIGINT
  - Stop accepting new requests
  - Wait up to 10s for in-flight requests to complete
  - Close cache, connections

### M4.4: Create environment template

- [ ] Create `.env.example`:
  - Document all required and optional environment variables
  - Include example values (no real secrets)
  - Comments explaining each variable

### M4.5: Create docker-compose for local dev

- [ ] Create `docker-compose.yml`:
  - FastAPI service
  - Sanity CMS mock (optional, for testing)
  - Volume for transcripts
  - Health checks

### M4.6: Update README with operations section

- [ ] Add "Operations" section to README.md:
  - Configuration reference
  - Health check commands
  - Metrics endpoints
  - Evaluation harness usage
  - Troubleshooting guide

## Acceptance Tests

- [ ] Missing environment variables cause immediate startup failure
- [ ] Health endpoint responds correctly for liveness and readiness probes
- [ ] Graceful shutdown completes within 10 seconds
- [ ] Rate limiting triggers at configured threshold
- [ ] README contains complete operations documentation

## Estimated File Changes

| File | Change |
|------|--------|
| `utils/config.py` | Create (env validation) |
| `middleware/ratelimit.py` | Create (rate limiting) |
| `server.py` | Modify (shutdown handlers, rate limit) |
| `.env.example` | Create (template) |
| `docker-compose.yml` | Create (local dev) |
| `README.md` | Modify (add operations section) |
| `tests/integration/test_config.py` | Create (config validation) |

## Done Means

- [ ] Missing environment variables cause immediate startup failure
- [ ] Health endpoint responds correctly for liveness and readiness probes
- [ ] Graceful shutdown completes within 10 seconds
- [ ] Rate limiting protects against abuse
- [ ] README contains complete operations documentation

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Circuit breaker | Prevents cascade failures during Sanity outages; simpler timeout-only approach would cause repeated failures | Repeated failures exhaust connection pools and degrade user experience |
| Rate limiting | Protects against accidental or malicious overload; simpler approach of no limits risks instability | Unlimited requests could overwhelm cache and cause DoS |
| Transcript recording | Required for evaluation harness and compliance; simpler logging without transcripts insufficient for replay | Replay capability essential for quality assurance |

## Research Notes

No Phase 0 research required. All technical decisions follow constitution principles and industry best practices for Python/FastAPI services. Dependencies (pydantic, tenacity, prometheus-client) are well-established libraries with proven reliability.
