# Feature Specification: Production-Grade Voice Agent

**Feature Branch**: `001-voice-agent-prod`
**Created**: 2026-02-11
**Status**: Draft
**Input**: User description: "Create a new spec named: sheriff-voice-agent-prod"

## Overview

Transform the existing Vapi-integrated phone agent from a prototype into a production-grade delivery tracking system suitable for real customer calls. This enhancement focuses on reliability, latency, observability, and evaluation capabilities without adding unnecessary complexity. The voice agent will continue handling delivery status inquiries but with enterprise-grade resilience and monitoring.

The current implementation accepts Vapi tool calls and queries Sanity CMS for delivery data. The production upgrade ensures this core function works consistently under load, recovers gracefully from failures, and provides transparency into system behavior for operators.

## Clarifications

### Session 2026-02-11

- **Q: Tracking ID field naming (camelCase vs snake_case)** → **A: Use camelCase everywhere (trackingNumber) for consistency with Sanity API and Vapi contracts**
- **Q: Security for health/metrics endpoints** → **A: Expose health/metrics on separate internal port (e.g., 8080) not exposed to public internet**
- **Q: Vapi timeout behavior when backend is slow** → **A: On timeout, agent reads cached delivery data (if available) with message about possible staleness**
- **Q: Circuit breaker manual override mechanism** → **A: HTTP admin endpoint on internal port (e.g., POST /admin/circuit-breaker/reset)**

## Out of Scope

The following are explicitly excluded from this feature:

- **Vector database or RAG implementation**: No semantic search or document embeddings
- **Multi-lingual support**: English-only voice interactions
- **SMS or text-based communication**: Voice-only channel
- **Payment processing or order modification**: Read-only delivery tracking only
- **Third-party carrier API integrations**: Sanity CMS remains the single data source
- **Custom voice model training**: Default Vapi voice configurations only

## Assumptions

- Sanity CMS provides authoritative delivery data with sub-minute update latency
- Vapi handles all speech-to-text and text-to-speech processing
- Voice call duration averages 60-90 seconds per inquiry
- Peak call volume estimated at 50 concurrent calls during business hours
- AWS App Runner or equivalent provides container hosting with auto-scaling
- Read-only Sanity token is sufficient for all delivery lookups

## User Scenarios & Testing

### User Story 1 - Check Delivery Status (Priority: P1)

A customer calls the delivery tracking hotline and asks for their package status. The agent validates the tracking number, queries the backend, and provides accurate status information without hallucinations or fabrication.

**Why this priority**: This is the primary use case representing 80% of calls. Without reliable status checks, the voice agent fails its core purpose.

**Independent Test**: Play a recorded voice call asking for delivery status and verify the agent returns verified data from the backend with correct formatting and no speculative information.

**Acceptance Scenarios**:

1. **Given** a valid tracking number exists in the system, **When** the caller requests status, **Then** the agent returns the exact status, customer name, and delivery estimate from verified backend data.

2. **Given** an invalid tracking number, **When** the caller requests status, **Then** the agent clearly states no delivery was found and suggests verifying the number.

3. **Given** a system error during backend query, **When** the caller requests status, **Then** the agent apologizes for the inconvenience and offers to retry.

---

### User Story 2 - Handle Delivery Issues (Priority: P2)

A customer calls about a delayed or problematic delivery. The agent retrieves any issue messages from the backend and communicates them clearly without adding speculation about resolution timelines.

**Why this priority**: Issue-related calls represent high-emotion situations where accurate information prevents customer frustration and support escalations.

**Independent Test**: Play a recorded call asking about a delayed package and verify the agent returns only the documented issue message without fabricating resolution promises.

**Acceptance Scenarios**:

1. **Given** a delivery has an associated issue message, **When** the caller asks about problems, **Then** the agent reads the exact issue text without modification or speculation.

2. **Given** no issue exists for a delivery, **When** the caller asks about problems, **Then** the agent states no issues are recorded and offers to check status instead.

---

### User Story 3 - Graceful Degradation Under Load (Priority: P2)

During backend slowdown or partial outages, the agent maintains acceptable user experience by using cached data when fresh data is unavailable, clearly communicating any limitations. If Vapi timeout is reached, cached data is returned with staleness notice.

**Why this priority**: Production systems experience failures; graceful degradation prevents complete service loss and maintains customer trust during incidents.

**Independent Test**: Simulate backend latency of 3+ seconds and verify the agent returns cached data within latency budget with staleness message, or clearly communicates temporary unavailability.

**Acceptance Scenarios**:

1. **Given** backend response exceeds 500ms, **When** a status check occurs, **Then** the response completes within 800ms total by using cached data with staleness notice.

2. **Given** Vapi timeout is reached (5s) with no cached data, **When** a status check occurs, **Then** the agent offers to retry without hanging up or returning errors.

3. **Given** backend is unavailable, **When** a status check occurs, **Then** the agent returns cached data if available with staleness notice.

---

### User Story 4 - Operator Observability (Priority: P3)

Support staff and engineers can view system health, recent errors, and performance metrics to diagnose issues during or after voice interactions.

**Why this priority**: Operational visibility is essential for maintaining service quality and troubleshooting problems in production.

**Independent Test**: Query the health endpoint and metrics endpoint to verify structured data is returned with correlation IDs for recent requests.

**Acceptance Scenarios**:

1. **Given** the service is running, **When** an operator queries `/healthz`, **Then** the response indicates `{"status": "ok"}` within 50ms.

2. **Given** the service is running, **When** an operator queries `/readyz`, **Then** the response includes dependency status for circuit breaker and Sanity CMS within 50ms.

3. **Given** the service is running, **When** an operator queries `/metrics`, **Then** the response is valid Prometheus format with counters for requests, cache, and errors.

4. **Given** a recent voice interaction occurred, **When** an operator searches logs by correlation ID, **Then** structured log entries show request timing, status, and any errors.

---

### Edge Cases

- Caller provides tracking number with special characters or spaces
- Tracking number exists but belongs to a different customer
- Backend returns malformed data structure
- Multiple concurrent calls during peak hours
- SANITY_API_TOKEN environment variable is missing
- Network partition between service and Sanity CMS
- Call drops during middle of response
- Vapi webhook timeout (5-second limit)

## Requirements

### Functional Requirements

- **FR-001**: System MUST return delivery status within 800ms P95 latency measured at webhook response time (from request receipt to response sent)
- **FR-002**: System MUST retry failed Sanity CMS requests with exponential backoff (max 3 attempts)
- **FR-003**: System MUST validate all incoming webhook payloads against expected schema
- **FR-004**: System MUST generate unique correlation ID for each request and include in all logs
- **FR-005**: System MUST return cached status data with staleness notice when backend latency exceeds 500ms or times out
- **FR-006**: System MUST NEVER fabricate delivery information; responses MUST derive from verified tool outputs
- **FR-007**: System MUST emit structured JSON logs with level, correlation ID, and timestamp
- **FR-008**: System MUST expose health endpoint for liveness/readiness checks on internal port (not public)
- **FR-009**: System MUST validate required environment variables at startup and fail fast if missing
- **FR-010**: System MUST record voice interaction transcripts and tool call results for replay evaluation
- **FR-011**: System MUST calculate and expose metrics: request latency, cache hit rate, error rate, tool success rate

### Key Entities

- **Delivery**: Core entity containing trackingNumber, status, customerName, customerPhone, estimatedDelivery, issueMessage
- **ToolCall**: Request record with correlationId, functionName, arguments, response, latency
- **CacheEntry**: Cached delivery status with TTL timestamp for cache invalidation
- **HealthStatus**: Aggregated system health including dependency status (Sanity CMS connectivity)

## Success Criteria

### Measurable Outcomes

- **SC-001**: 95% of voice interactions complete with verified data delivery (no hallucinations)
- **SC-002**: P95 latency for status queries remains under 800ms during normal operation
- **SC-003**: System maintains 99% availability during single Sanity CMS node failure
- **SC-004**: 60% of status queries served from cache during normal operation
- **SC-005**: 100% of production deployments pass health check validation before going live
- **SC-006**: Error rate during production operation remains below 1% of total requests
- **SC-007**: Evaluation harness can replay 100% of recorded voice interactions for accuracy scoring

## System Diagram

```
                        VOICE CALLER
                            |
                            v
                    +-------------+
                    |   Vapi      |  (speech-to-text, text-to-speech)
                    |   Platform  |
                    +------+------+
                           |
                           | HTTPS POST /webhook
                           v
                   +---------------+
                   |  FastAPI      |  (webhook handler)
                   |  Server       |
                   +-------+-------+
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
   +------------+  +--------------+  +--------------+
   |   Cache    |  |   Metrics    |  |   Structured |
   |   Layer    |  |   Collector |  |   Logger     |
   | (TTL 60s)  |  |              |  |              |
   +------+-----+  +------+-------+  +------+-------+
          |                |                |
          +----------------+----------------+
                           |
                           v
                   +---------------+
                   |   Sanity      |
                   |   CMS API     |
                   +---------------+
```

## Milestones

### Milestone 1: Foundation (Week 1)

Complete tool contract definition with Pydantic schemas and webhook payload validation. Establish logging infrastructure with correlation IDs and structured output.

**Deliverables**: Validated tool schemas, logging middleware, correlation ID propagation

### Milestone 2: Resilience (Week 2)

Implement retry logic with exponential backoff, circuit breaker pattern, and caching layer with TTL. Add timeout enforcement and graceful degradation paths.

**Deliverables**: Retry mechanism, circuit breaker, cache implementation, timeout configuration

### Milestone 3: Observability (Week 3)

Build health endpoints, metrics collection, and structured logging dashboard. Implement evaluation harness for transcript replay and scoring.

**Deliverables**: Health check endpoints, metrics API, log aggregation, evaluation runner

### Milestone 4: Hardening (Week 4)

Deploy hardening: environment validation, safe defaults, and production deployment scripts. Complete documentation and operational runbooks.

**Deliverables**: Env validation, deployment configs, documentation

## Acceptance Criteria

### Tool Contract Validation

- [ ] All webhook payloads validated against Pydantic schemas before processing
- [ ] Invalid payloads return 422 with descriptive error (no server exceptions)
- [ ] Schema violations logged with correlation ID for debugging

### Reliability

- [ ] Vapi timeout (5s) triggers cached data fallback with staleness message
- [ ] Sanity CMS retry succeeds for 95% of transient failures
- [ ] Circuit breaker opens after 5 consecutive failures and resets after 30 seconds
- [ ] HTTP admin endpoint (internal port) allows manual circuit breaker reset
- [ ] Graceful fallback returns cached or "try later" message without hanging
- [ ] Circuit breaker opens after 5 consecutive failures and resets after 30 seconds
- [ ] Graceful fallback returns cached or "try later" message without hanging

### Latency

- [ ] Cached status queries complete in under 500ms P50, 800ms P95
- [ ] Cache hit rate exceeds 60% during steady-state operation
- [ ] Timeout enforces 5-second maximum per upstream request

### Anti-Hallucination

- [ ] Agent responses contain only data from verified tool outputs
- [ ] Fallback responses clearly state "I don't have that information" (no speculation)
- [ ] 100% of fabricated responses caught in evaluation scoring

### Observability

- [ ] Every request logged with correlationId, latency, and status
- [ ] Health endpoint responds within 50ms (internal port only)
- [ ] Metrics exposed in Prometheus-compatible format (internal port only)

### Evaluation

- [ ] All voice interactions recorded with transcript and tool calls
- [ ] Replay tool can reproduce any past interaction deterministically
- [ ] Automated scoring identifies hallucination and latency regressions

### Deploy Hardening

- [ ] Missing environment variables cause immediate startup failure
- [ ] Health endpoint responds correctly for liveness and readiness probes
- [ ] Graceful shutdown completes within 10 seconds

## Risk List & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| Sanity CMS downtime | High | Medium | Implement aggressive caching with extended TTL during outages |
| Vapi webhook timeout (5s) | High | Low | Enforce 500ms internal timeout, return cached data or graceful fallback |
| Cache staleness causing wrong info | Medium | Low | Short TTL (60s), include data freshness indicator in responses |
| Evaluation harness complexity | Medium | Medium | Start with simple transcript capture; add scoring incrementally |
| Circuit breaker false positives | Low | Low | Conservative thresholds (5 failures), HTTP admin endpoint on internal port for manual reset |
| Correlation ID propagation gaps | Medium | Low | Validate correlation ID presence in all log entries during review |

## File/Module Impact Map

| File/Directory | Change Type | Description |
|----------------|------------|-------------|
| `server.py` | Modify | Add validation, caching, retry logic, observability |
| `requirements.txt` | Modify | Add pydantic, prometheus-client, tenacity for retries |
| `AGENTS.md` | Modify | Add production deployment guidelines |
| `tests/` | Create | Add contract tests, integration tests, evaluation fixtures |
| `scripts/` | Create | Add evaluation replay script, health check script |
| `.env.example` | Create | Document required environment variables |
| `docker-compose.yml` | Create | Local development with Sanity CMS mock |
