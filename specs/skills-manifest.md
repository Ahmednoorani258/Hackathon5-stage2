# Agent Skills Manifest: FlowSync Customer Success Digital FTE

This document formalizes the agent's modular skills for MCP/hackathon use. Each is an atomic, reusable capability that can be invoked independently, discovered via skill manifest, or orchestrated by an LLM or workflow engine.

| Skill Name               | When to Use                            | Inputs                                | Outputs                            | Description                                                                             |
|--------------------------|----------------------------------------|---------------------------------------|-------------------------------------|-----------------------------------------------------------------------------------------|
| Knowledge Retrieval      | Customer asks about product/features   | query: str                            | docs: list[str]                     | Retrieve relevant docs or FAQ for a query.                                              |
| Sentiment Analysis       | Every customer message                 | message: str                          | sentiment: float, confidence: float | Analyze customer mood to decide escalation, language, or followup.                      |
| Escalation Decision      | After generating a response            | context: dict (history, sentiment)    | should_escalate: bool, reason: str  | Decide if the issue should be escalated to human support or can be handled by the agent.|
| Channel Adaptation       | Before sending any response            | response: str, channel: str           | formatted: str                      | Format text appropriately for email/whatsapp/web.                                       |
| Customer Identification  | Every incoming message                 | metadata: dict (email/phone/etc)      | customer_id: str, history: dict     | Unify, lookup, merge customer record and history.                                       |

---

## Inputs/Outputs/Example Implementation (Pythonic reference only)

### Knowledge Retrieval Skill
- **When:** Customer asks a product question
- **Input:** `query: str`
- **Output:** `docs: list[str]`
- **Example implementation:**
  ```python
  def knowledge_retrieval(query: str) -> list[str]:
      """Return relevant doc snippets."""
      ...
  ```

### Sentiment Analysis Skill
- **When:** Every message
- **Input:** `message: str`
- **Output:** `sentiment: float`, `confidence: float`
- **Example:**
  ```python
  def sentiment_analysis(message: str) -> tuple[float, float]:
      ...
  ```

### Escalation Decision Skill
- **When:** After generating (draft) response
- **Input:** `context: dict` (conversation, messages, sentiment)
- **Output:** `should_escalate: bool, reason: str`
- **Example:**
  ```python
  def escalation_decision(context: dict) -> tuple[bool, str]:
      ...
  ```

### Channel Adaptation Skill
- **When:** Before responding on any channel
- **Input:** `response: str, channel: str`
- **Output:** `formatted_response: str`
- **Example:**
  ```python
  def channel_adaptation(response: str, channel: str) -> str:
      ...
  ```

### Customer Identification Skill
- **When:** On every inbound message
- **Input:** `metadata: dict (email, phone, etc)`
- **Output:** `customer_id: str, history: dict`
- **Example:**
  ```python
  def customer_identification(metadata: dict) -> tuple[str, dict]:
      ...
  ```

---

## Notes
- These skills are for the FlowSync FTE agent as described in the hackathon spec.
- They can be invoked by an orchestrator, agent, MCP server, or as part of a local workflow.
- *They are NOT Claude universal skills* (like /keybindings-help), but custom, agent-specific capabilities—matching the digital FTE hackathon framework.