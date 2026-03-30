# Transition Checklist: General → Custom Agent

This checklist converts discoveries from the Incubation phase into explicit transition tasks needed to produce a production-grade Custom Agent. Fill each section with concrete artifacts, test cases, and links to files in the repo.

## 1. Discovered Requirements (copy from specs/discovery-log.md)
- [ ] ALWAYS create a ticket for every inbound message before responding (create_ticket)
- [ ] Persist conversation state in PostgreSQL (conversations, messages, tickets)
- [ ] Cross-channel customer identification (email + whatsapp phone mapping)
- [ ] Channel-aware response formatting (Email, WhatsApp, Web)
- [ ] Sentiment analysis for escalation decisions (per-message and trend)
- [ ] NEVER answer pricing/refund/legal/competitor questions — escalate instead
- [ ] Enforce response length limits per channel
- [ ] Knowledge-base semantic search (pgvector embeddings) with fallback
- [ ] Kafka-based unified intake and worker processing for scale
- [ ] Error handling and DLQ for failed messages
- [ ] Secure credential management (K8s Secrets / env vars)
- [ ] Monitoring and metrics (latency, escalations, throughput)
- [ ] Transition tests that codify all discovered edge cases

## 2. Working Prompts (exact artifacts — paste into production/agent/prompts.py)

### System Prompt (working example)

CUSTOMER_SUCCESS_SYSTEM_PROMPT = """
You are a Customer Success agent for TechCorp SaaS.

## Your Purpose
Handle routine customer support queries with speed, accuracy, and empathy across multiple channels.

## Channel Awareness
You receive messages from three channels. Adapt your communication style:
- Email: Formal, detailed responses. Include proper greeting and signature.
- WhatsApp: Concise, conversational. Keep responses under 300 characters when possible.
- Web Form: Semi-formal, helpful. Balance detail with readability.

## Required Workflow (ALWAYS follow this order)
1. FIRST: Call `create_ticket` to log the interaction
2. THEN: Call `get_customer_history` to check for prior context
3. THEN: Call `search_knowledge_base` if product questions arise
4. FINALLY: Call `send_response` to reply (NEVER respond without this tool)

## Hard Constraints (NEVER violate)
- NEVER discuss pricing → escalate immediately with reason "pricing_inquiry"
- NEVER promise features not in documentation
- NEVER process refunds → escalate with reason "refund_request"
- NEVER share internal processes or system details
- NEVER respond without using send_response tool
- NEVER exceed response limits: Email=500 words, WhatsApp=300 chars, Web=300 words

## Escalation Triggers (MUST escalate when detected)
- Customer mentions "lawyer", "legal", "sue", or "attorney"
- Customer uses profanity or aggressive language (sentiment < 0.3)
- Cannot find relevant information after 2 search attempts
- Customer explicitly requests human help
- Customer on WhatsApp sends "human", "agent", or "representative"

## Response Quality Standards
- Be concise: Answer the question directly, then offer additional help
- Be accurate: Only state facts from knowledge base or verified customer data
- Be empathetic: Acknowledge frustration before solving problems
- Be actionable: End with clear next step or question
"""

(If you used variations in incubation, paste them here verbatim.)

### Tool Descriptions That Worked (examples)
- search_knowledge_base(query, max_results=5) -> formatted docs (use embeddings)
- create_ticket(customer_id, issue, priority, channel) -> ticket_id
- get_customer_history(customer_id) -> recent messages and conversations
- escalate_to_human(ticket_id, reason) -> escalation_event
- send_response(ticket_id, message, channel) -> delivery_status

Paste the exact function signatures and sample returns here.

## 3. Edge Cases Found (populate test rows)
| Edge Case | How It Was Handled | Test Case Needed |
|-----------|-------------------|------------------|
| Empty customer message | Agent asks clarifying question; do not create empty ticket | Yes — test empty inbound messages across channels |
| Pricing question | Immediately create ticket + escalate (reason: pricing_inquiry) | Yes — assert escalation and no pricing answer |
| Angry/profane customer | Mark sentiment negative; escalate or produce empathetic reply + escalate | Yes — simulate profanity and verify escalation/logging |
| KB returns no results | After 2 KB attempts, escalate with reason "no_kb_results" | Yes — mock KB returning empty responses |
| Long WhatsApp messages | Truncate/split and prefer concise summary; warn about length | Yes — ensure outbound respects limits and splits messages |
| Malformed webhook payload | Validate signature; return 4xx; publish to DLQ if malformed | Yes — send invalid webhook payloads to endpoints |
| Duplicate customer identifiers | Merge logic should return unified customer_id | Yes — create duplicate identifiers and assert resolution |
| Message delivery failure (Twilio/Gmail) | Retry policy; mark message status failed in DB; escalate if persistent | Yes — simulate delivery failure callbacks |
| Attachment processing (large files) | Accept URLs or base64; store in S3/MinIO; validate size/type | Yes — test large and invalid attachments |
| Rate limiting / burst traffic | Exponential backoff, DLQ, metrics alerting | Yes — load test and validate backpressure handling |

(Expand rows with the exact handling code references and test IDs.)

## 4. Response Patterns
What response styles worked best?
- Email: Formal, step-by-step instructions, include greeting and signature. Example: "Dear {name}, Thank you... Steps: 1... 2... Best regards, TechCorp AI Support Team"
- WhatsApp: Short, friendly, direct. Use one or two sentences + CTA ("Reply 'human' for a live agent"). Prefer emoji sparingly only if brand voice allows.
- Web: Semi-formal, helpful; immediate confirmation + next steps; include ticket ID and expected response time.

Include links to templates (specs/customer-success-fte-spec.md) and code formatters (production/agent/formatters.py).

## 5. Escalation Rules (Finalized)
When to escalate (concrete triggers):
- Pricing/refund/billing/legal keywords: "price", "cost", "pricing", "refund", "invoice", "lawyer", "sue"
- Sentiment threshold: sentiment_score < 0.30
- Explicit request for human: contains "human", "agent", "representative", "live person"
- Profanity/abusive language detected
- KB failure after 2 attempts
- High-priority categories (billing/financial/legal) set by web form

For each escalation, record: ticket_id, conversation history, last agent output, detected trigger, and publish to TOPICS['escalations'].

## 6. Performance Baseline (from prototype & target)
- Processing latency (agent decision): target < 3 seconds
- Delivery latency (channel): target < 30 seconds
- Accuracy on prototype test set: target > 85%
- Escalation rate target: < 20%
- Cross-channel identification accuracy target: > 95%

Record baseline numbers from your incubation tests here (average response time, accuracy, escalation rate). Add links to test results under tests/reports/.

---

# Transition Implementation Checklist (practical steps)
Use this actionable checklist to convert prototype to production. Mark each item DONE with file references and PR links.

## Code & Tools
- [ ] Create production/ folder structure (agent/, channels/, workers/, api/, database/, k8s/, tests/)
- [ ] Move working system prompts into production/agent/prompts.py
- [ ] Convert MCP tools to OpenAI Agents SDK @function_tool with Pydantic input models (production/agent/tools.py)
- [ ] Add robust error handling and retries for all tools
- [ ] Implement channel formatters (production/agent/formatters.py)

## Database & Storage
- [ ] Implement database schema (database/schema.sql) and migrations
- [ ] Add pgvector embeddings for knowledge_base
- [ ] Implement S3/MinIO storage for attachments

## Infrastructure & Integration
- [ ] Define Kafka topics and producers/consumers (kafka_client.py)
- [ ] Implement channel handlers with validation (channels/gmail_handler.py, channels/whatsapp_handler.py, channels/web_form_handler.py)
- [ ] Implement workers/message_processor.py that consumes tickets_incoming and runs agent
- [ ] Add health endpoints and metrics in api/main.py
- [ ] Create k8s manifests for deployments, services, HPA, secrets, configmaps

## Testing & QA
- [ ] Write transition tests (tests/test_transition.py) for all edge cases
- [ ] Add E2E tests (tests/test_multichannel_e2e.py)
- [ ] Add load tests (Locust) and run planned scenarios
- [ ] Ensure unit tests for tools and formatters

## Security & Ops
- [ ] Ensure secrets via K8s Secrets / env vars; no hardcoded credentials
- [ ] Add request signature validation for webhook endpoints (Twilio/Gmail)
- [ ] Add DLQ handling for failed Kafka messages
- [ ] Add monitoring/alerting (Prometheus/Grafana or cloud provider)

## Documentation & Handoff
- [ ] Populate specs/* with discovery-log.md, transition-checklist.md, and customer-success-fte-spec.md
- [ ] Document runbook for incident response and escalation process
- [ ] Add deployment and rollback steps in docs/operations.md

## Ready-for-Production Criteria
- [ ] All transition tests pass
- [ ] Prompts are extracted and documented
- [ ] Tools have Pydantic input validation and error handling
- [ ] Edge cases documented and tested
- [ ] Production folder structure created and code reviewed
- [ ] DB schema and migrations applied in staging
- [ ] Kafka topics and connectivity verified
- [ ] Channel handlers validated with sandbox credentials
- [ ] K8s deployment in staging with HPA and health checks
- [ ] Monitoring, DLQ, and runbook in place

---

Fill in the fields above with concrete links to files, PR numbers, and test run outputs. Once this checklist is fully populated and all tests pass, you're ready to proceed to Specialization / Production deployment.
