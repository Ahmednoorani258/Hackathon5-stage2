# FlowSync Support Escalation Rules

## Purpose
These rules define when the Digital FTE should **resolve** a ticket vs **escalate** to a human team (Support, Billing/RevOps, Security, Legal, or Product). The goal is to:
- Protect customers and FlowSync from risk
- Meet contractual obligations and SLAs
- Prevent unauthorized account or billing actions
- Ensure high-impact incidents receive rapid human attention

## Golden Rule
If any request involves **billing, legal, security, account access/ownership changes, data deletion/export at scale, or personal data**, **escalate**.

## Always-Escalate Trigger Keywords/Phrases
Escalate immediately if message includes any of the following (case-insensitive), even if customer seems calm:

### Legal / Threats
- “lawyer”, “legal action”, “sue”, “lawsuit”, “subpoena”, “attorney”, “regulator”
- “GDPR complaint”, “SOC 2 report demand”, “data breach claim”

### Billing / Payments / Refunds
- “refund”, “chargeback”, “dispute”, “unauthorized charge”, “invoice error”, “VAT”, “tax ID”, “PO”, “purchase order”
- “cancel my subscription” **because of billing**
- “change billing cycle”, “annual contract”, “pricing exception”, “discount”, “coupon”, “credit”

### Security / Access / Compliance
- “SSO”, “SAML”, “SCIM”, “audit log”, “DPA”, “data processing agreement”
- “breach”, “compromised”, “hacked”, “phishing”, “password reset for someone else”
- “transfer ownership”, “change admin”, “remove admin”, “account takeover”

### Privacy / Data Requests
- “delete all my data”, “erase”, “right to be forgotten”
- “export all data”, “all workspaces”, “all users”, “backup request”

### Severity / Service Down
- “down”, “outage”, “cannot access anything”, “all projects missing” with **high** priority or multiple users impacted

## Sentiment-Based Escalation Thresholds
If a sentiment model produces a score:
- **< 0.30 → Escalate** (very negative)
- **0.30–0.45 → Escalate if** repeated contact, high priority, or churn risk language
- **> 0.45 → Usually resolve** if within standard support scope

Escalate when customer expresses churn risk:
- “I’m cancelling”, “switching tools”, “we’re done”, “this is unacceptable”

## Topic Categories: Must Escalate vs Can Resolve

### Must Escalate
- **Billing** (all billing questions, invoices, refunds, disputes)
- **Legal threats / compliance demands**
- **Security incidents or suspected compromise**
- **Account ownership/admin changes**
- **Data deletion requests** (account/workspace)
- **Large data export requests** beyond self-serve (e.g., all-workspaces export)
- **Enterprise contract / SLA negotiations**

### Usually Can Be Resolved (Digital FTE)
- How-to guidance for tasks/projects/boards/timeline
- Notifications setup
- Basic integration setup (Slack, GitHub, Drive, Teams)
- Mobile app usage
- Troubleshooting common UI issues (cache, permissions, browser)
- Automations: enabling, creating simple rules, explaining limitations

### Escalate if Not Resolved in Two Rounds
If two troubleshooting attempts fail or the customer cannot reproduce steps, escalate with collected diagnostics.

## Priority-Based Escalation Timelines
- **High priority:** Escalate within **15 minutes** of identification; provide a mitigation suggestion immediately.
- **Medium priority:** Escalate within **2 hours**.
- **Low priority:** Escalate within **1 business day** if required.

## Required Escalation Handoff Package
When escalating, include:
- Ticket ID + channel + timestamp
- Customer identifiers (name, email; phone for WhatsApp)
- Workspace name (if provided)
- Plan/tier (if known) and billing status indicators
- Summary of issue in 2–3 bullets
- Exact customer wording for sensitive items (legal/security/billing quotes)
- Steps already attempted and results
- Screenshots/error text/log snippets (if provided)
- Suggested next action + recommended owner team

## Channel-Specific Rules

### WhatsApp
- If customer requests “**human**”, “**agent**”, “**live**”, “**someone call me**” → escalate.
- Keep clarifying questions minimal; ask for:
  - affected workspace/project
  - screenshot or error text
  - device (iOS/Android) and app version
- Avoid long policy explanations. Acknowledge and escalate quickly when required.

### Email
- Provide a structured summary and clear next steps.
- If escalation is required, confirm receipt and explain expected response window.

### Web Form
- Treat as an intake channel. If category is billing or message contains triggers, escalate.
- Otherwise respond with crisp steps and request missing details.

## Routing Logic (Who Receives What)
- **Billing/RevOps:** invoices, refunds, disputes, pricing, tax/VAT, contract changes
- **Security:** breach claims, compromised accounts, SSO/SAML/SCIM issues, privacy incidents
- **Legal:** threats, subpoenas, regulatory complaints
- **Product/Engineering:** confirmed bugs, outages, data integrity issues, integration failures beyond known fixes
- **Customer Success:** onboarding help for Enterprise, workspace design, adoption guidance when requested

## SLA Breach Rules
Escalate if:
- Enterprise ticket is approaching response SLA (within 30 minutes of target)
- Any high priority ticket has no progress after 2 hours
- Multiple tickets report the same outage symptom in a short time window

## Common Mistakes (What NOT to Escalate)
Do **not** escalate when:
- The customer needs basic “how do I…” guidance
- A single-user login issue can be solved by password reset guidance (without access takeover indicators)
- Notification preferences confusion
- Simple integration enabling steps (Slack/GitHub) unless OAuth errors persist
- Feature requests that can be recorded and acknowledged (escalate only if exec sponsor/Enterprise or legal/contract tied)
