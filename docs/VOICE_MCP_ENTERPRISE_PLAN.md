# West Bethel Voice AI & MCP Enterprise Plan

## Mission
Deliver a FAANG-caliber voice concierge for the West Bethel Motel that operates reliably across local development and GCP, backed by a robust MCP (Multi-Channel Platform) service exposing hotel availability, policy, and escalation tools.

---

## 1. Experience & Conversation Design

- **Personas & Journeys**
  - New guest, returning guest, urgent-issue caller.
  - Stages: greeting → intent discovery → slot capture → tool execution → confirmation/upsell → closure.
  - Metrics: intent classification latency, slot completion rate, self-service resolution, escalation rate.

- **Voice UX Principles**
  - Tone: warm, anticipatory, professional.
  - Turn-taking: immediate interrupt detection with resumable context.
  - Response design: <= 12 sec bursts, key facts first, optional detail prompts.
  - Recovery: graceful error prompts, DTMF fallback, compliance-safe language.

- **Dialog Assets**
  - Prompt library with variation control.
  - Persona guardrails (formal/informal, brand vocabulary).
  - Transition “bumper” scripts, edge-case phrases (sold out, maintenance).

- **Supporting Channels**
  - SMS/email follow-ups (summaries, booking links).
  - Internal dashboards for live transcript, intent confidence, tool output.

---

## 2. MCP Architecture & Deployment

- **Service Topology**
  - Modular endpoints: availability, lead capture, knowledge base, escalation routing.
  - REST/JSON (OpenAPI) with versioning, stateless design.
  - Environment parity: local Docker + `.env` support, Cloud Run in `us-central1`.

- **Data Integrations**
  - Real-time inventory API with caching and stale-if-error fallback.
  - CRM/lead storage, promotions/discount engine, knowledge base ingestion pipeline.

- **Security & Compliance**
  - Auth: signed JWT or OAuth between voice service and MCP.
  - Secret storage via GCP Secret Manager; rotation policy.
  - PII handling: masking in logs, retention/erasure SLAs, audit trails for tool use.

- **Observability**
  - Structured logging with Trace IDs.
  - Metrics: latency, error rate, request volume per tool.
  - Alerting thresholds: availability > 500 ms, error rate > 2%, auth failures.

---

## 3. Voice Agent Engineering Roadmap

### 3.1 Tool Contracts
| Tool | Purpose | Key Fields | Notes |
|------|---------|------------|-------|
| `check_availability` | Retrieve room inventory | `check_in`, `check_out`, `adults`, `pets`, `room_type`, `channel`, `session_id` | Response includes availability status, rates, upsell hints |
| `create_lead` | Capture prospect info | Guest PII, desired dates, contact preference | Idempotency via token |
| `generate_payment_link` | Send secure payment URL | Booking ID, amount, contact channel | PCI guardrails |
| `transfer_to_department` | Connect to human | Department, reason, transcript summary | Must log escalation |

### 3.2 Conversation Engine Enhancements
- State tracker for intents, slots, tool outcomes, escalation flags.
- Policy middleware validating tool usage (auth, throttling, data sanity).
- Barge-in support with partial transcription handling.
- Prompt templating system tied to persona guidelines.

### 3.3 Observability & Failover
- Unified trace across Twilio → Voice Bridge → Realtime API → MCP.
- Graceful degradation: record request + SMS callback if MCP or Realtime unavailable.
- Structured error taxonomy for analytics and alerting.

---

## 4. Testing & Quality Strategy

- **Automated**
  - Unit tests for tool clients, prompt utilities, state tracker.
  - Contract tests verifying MCP endpoint schemas.
  - Integration harness simulating Twilio media streams with seeded MCP data.
  - Load testing (peak concurrent calls) with latency/error assertions.
  - Chaos scenarios: MCP timeouts, Realtime disconnects, malformed responses.

- **Human Evaluation**
  - QA rubric for friendliness, accuracy, efficiency.
  - A/B testing of prompts and upsell strategies.
  - Transcript review workflow; flagged low-confidence calls for analysis.

---

## 5. Program Management & Governance

- Documentation: architecture diagrams, runbooks, change logs.
- RACI matrix covering conversation design, backend, DevOps, analytics.
- Change control: prompt/tool modifications require review + regression tests.
- Roadmap: quarterly objectives (loyalty integration, multilingual expansion).
- Security reviews: annual dependency audit, penetration tests for MCP endpoints.

---

## 6. Immediate Deliverables

1. **Architecture Spec**  
   - Sequence diagrams (voice → MCP), data flow maps, failure scenarios.

2. **API Contracts**  
   - OpenAPI schemas for availability, lead, payment tools.

3. **Local Development Tooling**  
   - Docker Compose / scripts to run MCP locally with seeded data.

4. **Observability Blueprint**  
   - Logging, tracing, metrics schema + dashboard mockups.

5. **Compliance Checklist**  
   - PII inventory, retention policy, incident response plan.

---

## 7. TDD Swarm Execution Plan

### Stage 1 – Foundation
1. Write failing contract tests for MCP availability endpoint (local stub).
2. Implement minimal MCP handler + pass tests.
3. Add client in voice function registry with unit tests mocking MCP responses.

### Stage 2 – Conversation Engine
1. TDD state tracker (intent, slots, tool outcomes).
2. TDD tool policy middleware (auth, rate limit, validation).
3. Integrate with Realtime client; add integration tests using simulated Twilio streams and mocked MCP.

### Stage 3 – Experience Polish
1. TDD prompt templating (variation control, persona compliance).
2. Add tests for interruption handling and fallback messaging.
3. Validate end-to-end flow with recorded audio fixtures.

### Stage 4 – Ops & Resilience
1. TDD logging/tracing helpers to ensure all paths emit trace IDs.
2. Chaos tests for MCP downtime → verify graceful fallback.
3. Deployment pipeline tests (Cloud Build) triggering smoke tests post-deploy.

Each swarm cycle:  
1. **Red** – write failing test reflecting desired capability.  
2. **Green** – implement minimal code to pass.  
3. **Refactor** – clean up, enforce standards, extend documentation.  
4. **Review** – cross-functional sign-off before merging.

---

## 8. Next Steps

- Schedule cross-functional workshop (product, ops, engineering, security).  
- Draft API spec for MCP `check_availability` and circulate for validation.  
- Prepare developer environment checklist (dependencies, secrets, Twilio sandbox).  
- Kick off Stage 1 TDD Swarm: contract tests for MCP availability endpoint, local Docker skeleton.  
- Establish shared dashboard & alerting requirements with DevOps/SRE.

This document is the living source of truth for the Voice AI & MCP initiative. Update alongside each milestone and reference during sprint planning, design reviews, and go-live readiness assessments.
