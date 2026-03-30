# claude.md

## Executive Summary

This repository implements a 24/7 multi-channel Customer Success Digital FTE (AI Full-Time Equivalent) as part of Agent Maturity Model Hackathon 5. It walks through all agent evolution phases: from Incubation (prototype/requirements discovery) to Specialization (production multi-channel deployment). The project uses the OpenAI Agents SDK, FastAPI, PostgreSQL, Kafka, and Kubernetes, and provides full modular architecture to operate autonomously across Email, WhatsApp, and Web Form channels.

---

## 1. Business Problem

SaaS clients require customer support with:
- 24/7 availability across **Email (Gmail)**, **WhatsApp**, and **Web Form**.
- Reliable escalation for pricing, legal, refunds, angry customers, or when the AI cannot resolve.
- Unified cross-channel ticket tracking, customer identification, and daily sentiment/performance reporting.
- Cost target: digital agent operates at < $1,000/year (vs human FTE at $75,000+).

---

## 2. Agent Maturity Model & Project Phases

| Phase            | Description                                                      | Artifacts/Checklist                                                                |
|------------------|------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Incubation**   | Prototype core agent, explore requirements via sample tickets,   | - specs/discovery-log.md<br>- MCP server<br>- Edge case doc<br>- Agent skills      |
|                  | document escalation patterns, channel differences.               |                                                                                    |
| **Transition**   | Convert proto to robust prod code: multi-channel, error-handled, | - production/* structure<br>- PostgreSQL CRM<br>- Transition test suite            |
|                  | modular, with full test coverage, using OpenAI Agents SDK.       | - specs/transition-checklist.md                                                    |
| **Specialization**| Reliable, scalable deployment. Kafka event-driven, channel      | - E2E tests<br>- K8s manifests<br>- Monitoring<br>- 24-hour multi-channel readiness|
|                  | integrations, K8s, monitoring, auto-scaling, reporting, runbook. |                                                                                    |

---

## 3. Multi-Channel Architecture

```plaintext
Gmail        WhatsApp       Web Form
 |              |               |
 V              V               V
 -------------Intake Handlers------------
 |          (API/Webhooks)              |
 ----------------|----------------------|
                V
             Kafka (Event Stream)
                V
         Unified Message Processor
                V
         Customer Success Agent
                V
        PostgreSQL-based CRM/Ticketing
                V
   Outbound via Gmail/Twilio/API Response
```

- **All channels** normalize to Kafka topics -> agent core -> CRM.
- Full roundtrip: Message intake → ticket creation → processing/response → CRM logging.

---

## 4. Folder / File Map

```
production/
├─ agent/                 # Agent logic, tools, prompts, formatters
├─ channels/              # Channel handlers: Gmail, WhatsApp, Web
├─ api/                   # FastAPI service
├─ database/              # schema.sql, queries, migrations
├─ workers/               # Kafka consumers, metrics, processors
├─ tests/                 # pytest suites: edge, channel, E2E logic
├─ k8s/                   # Kubernetes manifests (deploy, service, autoscale)
├─ Dockerfile, docker-compose.yml
└─ requirements.txt

# Key referenced files:
context/                  # company-profile.md, sample-tickets.json, escalation-rules.md, brand-voice.md
src/&, specs/             # discovery logs, crystallization, test checklists, prototype code
database/schema.sql       # full CRM schema (see Section 6)
tests/test_transition.py  # transition tests for all constraints & flows
```

---

## 5. Channel Specifications

| Channel   | Intake                | Student Implements      | Outbound/Reponse           | Formatting             | Max Length          |
|-----------|-----------------------|------------------------|----------------------------|------------------------|---------------------|
| Gmail     | Gmail API Webhook     | channels/gmail_handler.py | Gmail API send            | Formal, detailed       | 500 words           |
| WhatsApp  | Twilio WhatsApp API   | channels/whatsapp_handler.py | Twilio WhatsApp send      | Conversational, concise| 160 chars preferred (hard max 300 chars) |
| Web Form  | Next.js/HTML → FastAPI| channels/web_form_handler.py,<br>web-form/SupportForm.jsx | API response + email | Semi-formal         | 300 words           |

**NB:** All responses must match formatting/tone per channel. **Web Support Form (React)** is required deliverable.

---

## 6. CRM Database Schema (PostgreSQL, see database/schema.sql)

| Table                    | Key Fields                                                        | Notes                                            |
|--------------------------|-------------------------------------------------------------------|--------------------------------------------------|
| **customers**            | id, email, phone, name, created_at, metadata                     | Unified per person across all channels           |
| **customer_identifiers** | customer_id, identifier_type/value, verified                     | Cross-channel mapping                           |
| **conversations**        | customer_id, initial_channel, started_at, ended_at, status, sentiment_score | One per ongoing thread or interaction           |
| **messages**             | conversation_id, channel, direction, role, content, tokens_used, latency_ms, tool_calls | Tracks all inbound/outbound events               |
| **tickets**              | conversation_id, customer_id, source_channel, category, priority, status, resolved_at, notes | Always created at intake, never omitted         |
| **knowledge_base**       | id, title, content, category, embedding (vector)                 | Used for semantic/document search                |
| **agent_metrics**        | metric_name, metric_value, channel, dimensions, recorded_at       | For reporting, QA/QC, scaling metrics            |
| **channel_configs**      | channel, config, response_template, max_response_length          | For credentials and channel limits               |

---

## 7. Major Agent Flows

### a) Intake/Processing

1. **Message Intake:** Normalize from any channel; payload includes customer ID/email/phone, content, channel.
2. **Ticket Creation:** ALWAYS create a new ticket before any response.
3. **Customer/Multi-channel ID:** Map sender to unified customer (match email/phone).
4. **Conversation Memory:** Fetch customer’s cross-channel history.
5. **Sentiment Analysis:** Analyze mood; flag negative/abusive content.
6. **Knowledge Retrieval:** Search product docs via vector search (TOP 5 results, semantic).
7. **Escalation Check:** If pricing/legal/refunds/negative sentiment/etc., escalate before reply.
8. **Response Formatting:** Adapt content for target channel (length, tone, structure).
9. **Respond+Log:** Send outbound; log all fields/timestamps; update ticket status as appropriate.
10. **Metrics:** Log latency, escalation, feedback for reporting.

### b) Escalation Rules

Escalate (never answer) when:
- Customer asks about pricing, refund, legal, competitor.
- Sentiment < 0.3 OR profanity/hate detected.
- Customer explicitly requests human.
- WhatsApp messages "human/agent/representative".
- AI can't resolve after 2 failed knowledge base searches.

---

## 8. Agent Skills Manifest

| Skill/Tool                | When Used                                  | Inputs                          | Outputs                                  | Constraints/Notes                          |
|---------------------------|---------------------------------------------|----------------------------------|------------------------------------------|---------------------------------------------|
| search_knowledge_base     | Product/feature Qs                          | query:str, max_results:int      | relevant docs (max 5)                    | Vector search, fallback message on failure  |
| create_ticket             | EVERY INTAKE                                | customer_id, issue...           | ticket_id                                | Required before any agent response          |
| get_customer_history      | Before reply                                | customer_id                     | cross-channel interaction summary         | Always check before responding              |
| escalate_to_human         | See rules above                             | ticket_id, reason               | escalation_id or reference               | Always include context/reason               |
| send_response             | EVERY REPLY                                 | ticket_id, message, channel     | delivery_status, channel_message_id       | All channel formatting rules apply          |

- **Channel Adaptation**: Embedded in send_response/formatter
- **Customer Identification**: Message metadata mapping (IDs, phone, email, etc.)

---

## 9. Hard Constraints / Guardrails

- **MUST:** Create a ticket before replying, always check sentiment, always format for channel.
- **MUST NOT:** Answer pricing/legal/refunds/competitor questions; never skip logs/DB writes; never violate channel length/formatting.
- **NEVER:** Hardcode credentials.
- **Response limits:** Email ≤ 500 words, WhatsApp ≤ 300 chars (preferred; max 1600), Web ≤ 300 words.

---

## 10. Testing and Verification

**Transition Test Suite**: See `tests/test_transition.py`
- Edge case coverage (empty message, pricing escalation, anger/sentiment, channel formatting, tool call order).
- Run pytest end-to-end across all inbound channels.
- Coverage: Ticket must exist for all messages; response formatting per channel; escalation triggers; conversation cross-channel continuity.

**Integration/E2E**: See `tests/test_multichannel_e2e.py`
- Multi-channel form/email/whatsapp ticketing and retrieval.
- Channel metric accuracy.

**Load Testing**: See `tests/load_test.py` (Locust).
- Must pass: 100+ web, 50+ email/whatsapp, >=10 cross-channel, 24hr CHAOS/uptime test.

**Production Verification:**
- K8s manifests deployed and functional (auto-scale, health checks, K8s/Ingress).
- Metrics: uptime >99.9%, P95 latency <3s/ch, escalation <25%, no data loss, cross-channel match >95%.

---

## 11. Channel-by-Channel Integration and Format Requirements

| Channel   | Intake Handler           | Outbound Method       | Required Response Quality            | Verification             |
|-----------|-------------------------|----------------------|--------------------------------------|--------------------------|
| Gmail     | Gmail API Webhook       | Gmail API send       | Greeting, signature, formal style    | End-to-end test/email logs|
| WhatsApp  | Twilio Webhook          | Twilio send          | Short, conversational, emoji-OK      | WhatsApp test, delivery status|
| Web Form  | FastAPI, React          | API response + email | Concise, clear, helpful, semi-formal | Web/E2E form submission, ticket API|

---

## 12. Common Errors & Transition Checklists

**Common Transition Mistakes**
- Skipping documentation/specs.
- Copy-pasting prototype code unrefactored.
- Ignoring edge cases/tests.
- Hardcoding non-secret values (config required).
- Skipping full error handling in channel handlers.
- Not matching channel-specific formatting.

**Transition Complete Criteria**
- All transition tests pass.
- Full prompts and specs extracted to code/docs.
- Tools use Pydantic for validation, @function_tool everywhere.
- Edge cases codified.
- Folder structure matches production standard.
- All environment variables/configs externalized.

---

## 13. Reference / Further Reading

- Key files: `production/agent/`, `production/channels/`, `database/schema.sql`, `production/api/`, `tests/`, `specs/`.
- Required Reading:
  - Agent Maturity Model: [Panaverse Docs](https://agentfactory.panaversity.org/docs/General-Agents-Foundations/agent-factory-paradigm/the-2025-inflection-point#the-agent-maturity-model)
  - OpenAI Agents SDK
- *context/*.md: Company, product, and sample ticket docs.
- **FAQ**: PostgreSQL IS your CRM; only support form, not full site, is required; sandbox (Gmail, Twilio) is permitted; Web form is required, WhatsApp/Gmail partial allowed if documented.

---

## 14. Deliverable/Integration Checklist

- [ ] Prototype agent, skills, and MCP tools built and tested
- [ ] CRM schema in PostgreSQL with all core tables and indexing
- [ ] All channel handlers implemented (Gmail, WhatsApp, Web)
- [ ] Kafka event streaming flows with channel-aware topics
- [ ] Kubernetes manifests (deployments, HPA, services, secrets)
- [ ] Web Support Form (Next.js React) with validation, ticket tracking
- [ ] End-to-end transition and multichannel tests pass
- [ ] Uptime/load tested for 24h, chaos and recovery tests
- [ ] Documentation updated in claude.md for onboarding and future agent work

---

**With this claude.md, new developers or agents can rapidly onboard, verify requirements, and extend or operate the Digital FTE system without consulting lengthy external docs.**

---

*For implementation, reference this document, the context/* and specs/* directories, and the codebase for up-to-date conventions, patterns, and regulatory guardrails.*
