# Discovery Log (Incubation / Exploration)

## Channel Patterns Discovered

### Email (Gmail)
- **Length & structure:** Longer, formal, multi-paragraph. Often includes environment details (browser, workspace, project) and a clear request.
- **Tone:** Professional and patient, but can escalate sharply when business impact is high.
- **Typical asks:** Step-by-step troubleshooting, capability questions, “how-to” guidance, and enterprise admin topics.
- **Signal quality:** High—customers frequently include workspace/project context and prior steps tried.

### WhatsApp
- **Length & structure:** Short, casual, sometimes incomplete. Often one-liners (“not working”), slang/abbreviations (“r”, “pls”), and occasional non-English phrases.
- **Tone:** Conversational, urgency-heavy. Emotional language appears more often.
- **Signal quality:** Variable—some messages have almost no context; others include succinct symptom + impact.
- **Behavioral cues:** Direct human requests appear (“need human pls”). Emojis are common and should be mirrored lightly (max 1–2).

### Web Form
- **Length & structure:** Medium length, relatively structured. Typically states the intent clearly but may omit technical diagnostics.
- **Tone:** Professional and “intake-like.”
- **Signal quality:** Moderate—often enough to route correctly and respond with initial steps.
- **Useful field dependency:** Subject + category help drive routing; still need follow-up questions for missing basics.

## Common Issue Categories
Top recurring issue clusters (mapped from the 60 tickets):
1. **Performance / access incidents (technical, high priority)**
   - Slow boards/freezing, cannot access workspace, blank pages, projects missing.
2. **Billing & pricing (billing, high priority)**
   - Annual vs monthly, invoices, VAT, double charges, refunds, invoice corrections.
3. **Notifications (technical/general, low–medium priority)**
   - Duplicate notifications, too many emails, push notifications not received.
4. **Integrations & automations (technical, medium priority)**
   - Slack not posting, GitHub task status not updating, automation rules not firing.
5. **Admin/permissions & governance (technical/general, medium–high)**
   - Cannot manage members, ownership transfer, SSO (Enterprise), deletion/export requests.

## Escalation Patterns

### Most frequent escalation triggers (observed)
- **Billing keywords:** refund, charged twice, invoice, VAT, annual billing, invoice reissue.
- **Enterprise auth/security topics:** SSO/SAML looping; compliance docs (SOC 2, DPA).
- **Legal threat language:** “lawyer” appears explicitly and should trigger immediate escalation.
- **Potential incident signals:** multi-user impact, “whole team blocked,” “all projects missing,” “service is slow,” “blank page”.
- **Churn risk:** “we will cancel/switch tools” tied to outage/performance/access.
- **Data risk:** missing comments, projects missing (data integrity), full workspace export, deletion requests.
- **Channel-specific human handoff:** WhatsApp “need human pls”.

### Escalation vs resolve boundary (working rule)
- **Resolve:** how-to, standard troubleshooting, common settings issues, basic integrations and automation checks.
- **Escalate:** billing/pricing/refunds, legal/security/compliance, ownership/admin transfer, large export/deletion, suspected data loss, outages/multi-user performance incidents, Enterprise SSO.

## Edge Cases Found
- **Near-empty messages:**
  - WhatsApp: “not working” (ticket_040)
  - Web form: “help” with missing contact fields (ticket_059)
  - Requires a single clarifying question + minimal required identifiers.
- **Mixed language:** Spanish and Portuguese in WhatsApp (tickets_022, _030).
- **Missing identifiers:** anonymous WhatsApp and empty web form fields require careful triage without over-collecting.
- **Sensitive domains:** healthcare operations context + legal threat (ticket_017) increases urgency and risk.
- **Data integrity suspicion:** “comments disappeared”, “projects missing”, “tasks revert” requires escalation even if not proven.

## Cross-Channel Continuity Opportunities
Examples where continuity should be preserved in the CRM:
- **CandorHealth cluster:**
  - Email legal threat/access lockout (ticket_017)
  - WhatsApp urgent access + cancel threat (ticket_037)
  - Web form blank page access issue (ticket_052)
  - Opportunity: auto-link by email domain + workspace name; treat as a single incident thread.
- **HoneycombApps SSO cluster:**
  - Email SSO loop (ticket_019)
  - WhatsApp SSO loop (ticket_039)
  - Web form Enterprise SSO (ticket_053)
  - Opportunity: merge into one escalation case with aggregated diagnostics.
- **AtlasOps ownership transfer:**
  - Email ownership transfer request (ticket_014)
  - WhatsApp follow-up request (ticket_038)
  - Opportunity: unify identity and prevent repeated verification steps.
- **Cobalt Agency refund follow-up:**
  - Email refund request (ticket_004)
  - Web form follow-up (ticket_060)
  - Opportunity: show last update status and avoid re-asking for invoice details.
- **NorthPeak AI pricing:**
  - Email upgrade questions (ticket_003)
  - Web form annual invoice request (ticket_045)
  - Opportunity: hand off to Billing once, then reuse the same case.

## Recommendations for Agent Behavior

1. **Start with channel-appropriate framing**
   - Email: structured summary + numbered steps + request for missing env details.
   - WhatsApp: one short question at a time; confirm the symptom category quickly.
   - Web form: acknowledge subject/category; provide the shortest path to resolution.

2. **Escalate early for policy-sensitive categories**
   - Billing, legal, security, privacy, ownership, deletion, full export, enterprise SSO.
   - In escalation responses, clearly state: “I’m escalating this to {team}” + expected timeline.

3. **Minimize back-and-forth in high-impact incidents**
   - For “team blocked / outage” tickets: provide immediate mitigation suggestions (refresh, incognito, check filters) while initiating escalation.

4. **Use a consistent minimal diagnostic checklist for technical issues**
   - Workspace name
   - Project name (if relevant)
   - Web vs desktop vs mobile
   - Browser/app version
   - Exact error text or screenshot
   - Time window + number of impacted users

5. **Implement cross-channel identity & thread merging rules (future CRM logic)**
   - Merge by exact email; then by domain + workspace name; then by phone number for WhatsApp.
   - Flag “possible match” when confidence is medium to avoid incorrect merges.

6. **Handle near-empty inputs safely**
   - Ask a single multiple-choice style clarification (load vs login vs save vs notifications) and request one identifier.

7. **Preserve brand voice constraints**
   - Avoid blaming language.
   - Avoid “ASAP”; use specific time expectations.
   - Use emojis only on WhatsApp and max 1–2.

## Questions That Need Clarification (if any)
1. **Self-serve vs escalation for data export:** Is “full workspace export” always manual, or will there be an Enterprise self-serve export feature?
2. **Verification standards:** What are the exact requirements to approve ownership transfer and deletion requests (e.g., proof of domain ownership, billing verification, admin confirmation)?
3. **Incident communications:** Should the Digital FTE reference a status page or internal incident number in customer-facing responses?
4. **Billing policy:** Are partial refunds, proration, and annual↔monthly changes allowed automatically, or only via Billing/RevOps?

## Suggested Next Steps for Prototype (Exercise 1.2)
1. Define the **canonical CRM entities** needed for continuity: Customer, Workspace, Ticket, ConversationThread, ChannelMessage, EscalationCase.
2. Draft **triage classification outputs** the agent must produce for every message:
   - intent, category, priority, sentiment, expected_action, required_fields_missing, suggested_next_questions.
3. Implement retrieval strategy for product docs (later):
   - chunking rules + embeddings + pgvector index + citation strategy.
4. Prototype the **escalation handoff template** (structured JSON) and validate with stakeholders.
5. Build a small “conversation continuity” simulation using the provided cross-channel clusters.
