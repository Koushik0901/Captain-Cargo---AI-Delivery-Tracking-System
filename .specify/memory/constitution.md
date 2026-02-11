<!--
SYNC IMPACT REPORT
==================
Version change: N/A → 1.0.0 (initial creation)

Modified principles: N/A (new constitution)
Added sections:
- 7 Core Principles (Deterministic Tool Contracts, Reliability, Latency Discipline,
  Hallucination Control, Observability, Evaluation Harness, Deploy Hardening)
- Additional Constraints (Performance Standards, Technology Stack)
- Development Workflow

Removed sections: N/A

Templates requiring updates:
- .specify/templates/plan-template.md ✅ aligned (Constitution Check references constitution)
- .specify/templates/spec-template.md ✅ aligned (User stories + requirements sections)
- .specify/templates/tasks-template.md ✅ aligned (testable, independently deliverable tasks)

Follow-up TODOs: None
-->

# Captain Cargo Constitution

## Core Principles

### I. Deterministic Tool Contracts (NON-NEGOTIABLE)

All Vapi tool calls MUST use strict Pydantic input/output schemas. Every tool MUST define:
- Explicit parameter types with validation rules
- Structured response formats with status indicators
- Clear error response contracts

Tool calls must be deterministic: same inputs always produce same structured outputs.
Rationale: Voice agents require predictable tool behavior for reliable user experiences.

### II. Reliability (NON-NEGOTIABLE)

All external calls MUST implement:
- Retry with exponential backoff for transient failures
- Configurable timeouts (5s default for synchronous tool calls)
- Idempotency where applicable
- Graceful fallback responses when upstream services fail

Critical paths must handle partial failures without cascading to user-visible errors.
Rationale: Voice calls cannot recover from dropped requests; users hang up on errors.

### III. Latency Discipline (NON-NEGOTIABLE)

Status lookups MUST implement:
- In-memory caching with configurable TTL (60s default for delivery status)
- Time budgets per request component (Vapi → webhook ≤ 500ms)
- Clear degradation when upstream is slow (return cached stale data if configured)
- No blocking I/O in async code paths

Rationale: Voice agents require sub-second response times; latency destroys user trust.

### IV. Hallucination Control (NON-NEGOTIABLE)

Agent responses MUST be derived only from verified tool outputs:
- If tool succeeds: respond with tool-verified data only
- If tool fails: transparently communicate failure to user, do not fabricate
- No speculative information in response text
- Fallback responses must clearly state limitations

Rationale: Voice agents making up delivery information cause real-world user harm.

### V. Observability (NON-NEGOTIABLE)

All operations MUST emit structured telemetry:
- Correlation IDs trace requests end-to-end
- Structured JSON logs at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Basic metrics: latency p50/p95/p99, error rate, cache hit ratio
- Health endpoint for liveness/readiness checks

Rationale: Production voice agents require immediate debugging during live calls.

### VI. Evaluation Harness (NON-NEGOTIABLE)

Must support replay-based evaluation:
- Transcript/utterance replay capability for all Vapi interactions
- Automated scoring: accuracy, tool success rate, latency percentiles
- Regression detection for tool call success rates
- Test fixtures for common delivery scenarios

Rationale: Voice agent quality degrades silently without automated evaluation.

### VII. Deploy Hardening (NON-NEGOTIABLE)

Production deployments MUST:
- Validate required environment variables at startup (fail fast)
- Health endpoints for Kubernetes/liveness probes
- Graceful shutdown handling
- Default to safe, conservative configurations
- Feature flags for experimental changes

Rationale: Voice agents have zero tolerance for deployment-related downtime.

## Additional Constraints

### Performance Standards

- P95 latency budget: 800ms total (Vapi → webhook → response)
- P99 latency budget: 1500ms (with degradation after 500ms)
- Cache hit ratio target: ≥ 60% for status lookups
- Error rate threshold: ≤ 1% for production deployments

### Technology Stack

- Backend: FastAPI with Python 3.9+
- Voice Platform: Vapi (tool-call pattern)
- Database: Sanity.io (structured content)
- Deployment: AWS App Runner or equivalent container platform
- All credentials via environment variables (no hardcoded secrets)

### Security Requirements

- Never expose API tokens in logs or error messages
- Parameterized queries only (no f-string concatenation in GROQ queries)
- HTTPS required for all production endpoints
- Read-only Sanity tokens for delivery tracking

## Development Workflow

All changes MUST:
1. Pass constitution validation before code review
2. Include tests for new tool contracts (contract tests required)
3. Document latency/performance impact for user-facing changes
4. Include rollback procedure for production deployments
5. Update observability dashboards for new metrics

Code review MUST verify:
- Tool schemas are deterministic and versioned
- Error handling follows fallback patterns
- Latency requirements are met or justified
- Observability logging is present and appropriate

## Governance

This constitution supersedes all other development practices in this repository. All PRs and reviews MUST verify compliance with these principles. Complexity MUST be justified against voice-agent quality requirements.

Amendments require:
1. Documentation of proposed changes with rationale
2. Migration plan for existing deployments
3. Review and approval from project maintainers

Refer to `AGENTS.md` for runtime development guidance.

**Version**: 1.0.0 | **Ratified**: 2026-02-11 | **Last Amended**: 2026-02-11
