# Tasks: Production-Grade Voice Agent

**Input**: Design documents from `/specs/001-voice-agent-prod/`
**Prerequisites**: plan.md, spec.md

**Tests**: Included per task (unit, integration, contract tests)

**Organization**: Tasks grouped by user story for independent implementation and testing

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- `tests/` at repository root (single FastAPI project)
- `models/`, `services/`, `middleware/`, `utils/`, `endpoints/`, `scripts/` directories
- Paths assume repository root context

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create directory structure: `models/`, `services/`, `middleware/`, `utils/`, `endpoints/`, `scripts/`, `tests/unit/`, `tests/contract/`, `tests/integration/`
- [x] T002 Add dependencies to `requirements.txt`: `pydantic>=2.0`, `tenacity`, `prometheus-client`, `pytest`, `pytest-asyncio`, `httpx`
- [x] T003 [P] Create `models/__init__.py` with module exports
- [x] T004 [P] Create `services/__init__.py` with module exports
- [x] T005 [P] Create `middleware/__init__.py` with module exports
- [x] T006 [P] Create `utils/__init__.py` with module exports
- [x] T007 [P] Create `endpoints/__init__.py` with module exports
- [x] T008 [P] Create `tests/__init__.py`, `tests/unit/__init__.py`, `tests/contract/__init__.py`, `tests/integration/__init__.py`

**Checkpoint**: Directory structure ready, dependencies installed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational (Write First - Ensure Fail) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T009 [P] Contract test for tracking ID normalization in `tests/unit/test_normalization.py`
- [x] T010 [P] Contract test for Pydantic webhook models in `tests/contract/test_webhook_schemas.py`

### Implementation for Foundational

- [x] T011 Create `utils/normalization.py` with `normalize_tracking_id(raw_id: str) -> str` function
- [x] T012 Create `models/webhook.py` with Pydantic v2 models
- [x] T013 Create `models/delivery.py` with Delivery entity models
- [x] T014 Create `middleware/correlation.py` for correlation ID propagation
- [x] T015 Create `utils/logger.py` for structured JSON logging
- [x] T016 Create `services/response_builder.py` for hallucination-safe responses

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Check Delivery Status (Priority: P1) 🎯 MVP

**Goal**: Enable customers to call and receive accurate delivery status information

**Independent Test**: Send Vapi webhook with valid tracking ID, verify response contains only verified backend data with correct structure

### Tests for User Story 1 (Write First - Ensure Fail) ⚠️

- [x] T017 [P] [US1] Unit test for `fetch_from_sanity` success path in `tests/integration/test_delivery_fetch.py`
- [x] T018 [P] [US1] Unit test for `fetch_from_sanity` not-found path in `tests/integration/test_delivery_fetch.py`
- [x] T019 [P] [US1] Integration test for `/webhook` endpoint with valid tracking ID in `tests/integration/test_webhook.py`

### Implementation for User Story 1

- [x] T020 [US1] Create `services/sanity_client.py` for Sanity CMS communication
- [x] T021 [US1] Update `server.py` to integrate with new modules
- [x] T022 [US1] Add validation middleware in `middleware/validation.py`

**Checkpoint**: User Story 1 complete - voice agent can answer delivery status queries

---

## Phase 4: User Story 2 - Handle Delivery Issues (Priority: P2)

**Goal**: Enable customers to receive documented issue messages without speculation

**Independent Test**: Send Vapi webhook with tracking ID that has an issue, verify response reads exact issue text without modification

### Tests for User Story 2 (Write First - Ensure Fail) ⚠️

- [x] T023 [P] [US2] Unit test for issue message extraction in `tests/unit/test_issue_handling.py`
- [x] T024 [P] [US2] Integration test for issue response formatting in `tests/integration/test_issue_response.py`

### Implementation for User Story 2

- [x] T025 [US2] Enhance `services/response_builder.py` with issue-specific methods
- [x] T026 [US2] Update `server.py` to route issue queries

**Checkpoint**: User Story 2 complete - issue queries handled accurately

---

## Phase 5: User Story 3 - Graceful Degradation (Priority: P2)

**Goal**: Maintain user experience during backend slowdowns or outages

**Independent Test**: Simulate Sanity CMS latency >3s, verify cache fallback or graceful unavailability within 800ms

### Tests for User Story 3 (Write First - Ensure Fail) ⚠️

- [x] T027 [P] [US3] Unit test for TTL cache expiration in `tests/unit/test_cache.py`
- [x] T028 [P] [US3] Integration test for retry with exponential backoff in `tests/integration/test_retry.py`
- [x] T029 [P] [US3] Integration test for fallback response in `tests/integration/test_fallback.py`

### Implementation for User Story 3

- [x] T030 [US3] Create `services/cache.py` with TTL cache
- [x] T031 [US3] Enhance `services/sanity_client.py` with retry and circuit breaker
- [x] T032 [US3] Create `middleware/timeout.py` for timeout enforcement
- [x] T033 [US3] Enhance `services/response_builder.py` with fallback methods
- [x] T034 [US3] Update `server.py` to use cache and fallbacks

**Checkpoint**: User Story 3 complete - system degrades gracefully under load

---

## Phase 6: User Story 4 - Operator Observability (Priority: P3)

**Goal**: Enable operators to monitor system health and debug issues

**Independent Test**: Query `/healthz` and `/metrics`, verify structured responses with correct format

### Tests for User Story 4 (Write First - Ensure Fail) ⚠️

- [x] T035 [P] [US4] Unit test for health endpoint response format in `tests/unit/test_health.py`
- [x] T036 [P] [US4] Unit test for metrics endpoint Prometheus format in `tests/unit/test_metrics.py`

### Implementation for User Story 4

- [x] T037 [US4] Create `endpoints/health.py` with health endpoints
- [x] T038 [US4] Create `endpoints/metrics.py` with Prometheus metrics
- [x] T039 [US4] Update `middleware/correlation.py` to include metrics collection

**Checkpoint**: User Story 4 complete - operators have health and metrics visibility

---

## Phase 7: Evaluation Harness (Priority: P3)

**Goal**: Enable quality assurance through transcript replay and scoring

**Independent Test**: Run eval harness on sample transcripts, verify accuracy and latency scoring output

### Implementation for Evaluation Harness

- [x] T040 Create `middleware/recording.py` for transcript recording
- [x] T041 Create `scripts/eval_replay.py` evaluation harness

**Checkpoint**: Evaluation harness complete - replay and scoring available

---

## Phase 8: Deploy Hardening (Priority: P3)

**Goal**: Production-ready deployment with proper configuration and documentation

### Implementation for Deploy Hardening

- [x] T042 Create `utils/config.py` for environment validation
- [x] T043 Create `middleware/ratelimit.py` for rate limiting
- [x] T044 Update `server.py` with graceful shutdown
- [x] T045 Create `.env.example` environment template
- [x] T046 Create `docker-compose.yml` for local development
- [x] T047 Update `README.md` with operations section

**Checkpoint**: Deploy hardening complete - production deployment ready

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - delivers core MVP
- **User Story 2 (Phase 4)**: Depends on Foundational - issue handling
- **User Story 3 (Phase 5)**: Depends on Foundational - resilience patterns
- **User Story 4 (Phase 6)**: Depends on Foundational - observability
- **Evaluation (Phase 7)**: Depends on User Story 1 completion
- **Deploy Hardening (Phase 8)**: Depends on all user stories

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories - **DELIVER MVP FIRST**
- **User Story 2 (P2)**: Can start after Foundational - Independent of US1
- **User Story 3 (P2)**: Can start after Foundational - Independent of US1, US2
- **User Story 4 (P3)**: Can start after Foundational - Independent of US1, US2, US3

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- User Stories 2, 3, 4 can proceed in parallel after Foundational
- All tests for a user story marked [P] can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test delivery status queries
5. Deploy/demo MVP

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy (MVP!)
3. Add User Story 2 → Test independently → Deploy
4. Add User Story 3 → Test independently → Deploy
5. Add User Story 4 → Test independently → Deploy
6. Add Evaluation → Deploy
7. Add Deploy Hardening → Production ready

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (core delivery lookup)
   - Developer B: User Story 3 (resilience - cache, retry, fallback)
   - Developer C: User Story 4 (observability - health, metrics)
3. Stories complete and integrate independently

---

## Notes

- **[P]** tasks = different files, no dependencies
- **[USX]** label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Task Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1: Setup | T001-T008 | Directory structure and dependencies |
| Phase 2: Foundational | T009-T016 | Models, validation, correlation IDs, logging |
| Phase 3: US1 - Delivery Status | T017-T022 | Core delivery lookup |
| Phase 4: US2 - Issue Handling | T023-T026 | Issue message delivery |
| Phase 5: US3 - Degradation | T027-T034 | Cache, retry, fallback |
| Phase 6: US4 - Observability | T035-T039 | Health, metrics |
| Phase 7: Evaluation | T040-T041 | Replay and scoring |
| Phase 8: Deploy Hardening | T042-T047 | Config, rate limit, docs |

**All 47 Tasks Completed**
