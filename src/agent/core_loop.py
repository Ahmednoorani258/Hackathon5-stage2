import re
import time
from typing import Dict, Any

# --- Simple product docs keywords (later, swap with embeddings or chunked search) ---
PRODUCT_FAQ = [
    ("Invite teammates", "To invite a teammate: Workspace → Members → Invite → Enter emails → Send invites."),
    ("Timeline empty", "Timeline requires tasks to have both start and due dates. Use filters to find missing dates."),
    ("Refunds", "Billing and refund requests are escalated to our RevOps team. Please provide invoice details."),
    ("Notifications", "Manage notifications: Settings → Notifications. Disable unwanted email alerts here."),
    ("SSO/SAML", "Enterprise customers may sign in via SSO/SAML. Issues may require IT/admin review."),
    ("Permissions error", "Only Owners can invite members. Contact your Owner to update your role."),
]

# --- Escalation keywords based on rules ---
ESCALATION_KEYWORDS = [
    r"refund", r"dispute", r"invoice", r"chargeback", r"sue", r"lawyer", r"legal", r"VAT", r"tax", r"compli", r"SSO", r"SAML", r"breach", r"takeover", r"delete.*account", r"GDPR", r"ownership transfer", r"pricing", r"cancel (my )?subscription", r"switching tools", r"this is unacceptable", r"representative", r"human", r"agent", r"live", r"annual contract"
]

CHANNEL_LIMITS = {
    "email": 5000,
    "whatsapp": 300,
    "web_form": 1500
}

CHANNEL_TEMPLATES = {
    "email": lambda customer, content: f"Hello {customer or 'there'},\n\n{content}\n\nBest regards,\nFlowSync Customer Success Team", # More formal and consistent
    "whatsapp": lambda customer, content: (
        content.split(". ")[0][:160] + (" 🙂" if len(content)<120 else "")
        if len(content) > 180 else content + (" 🙂" if len(content)<110 else "")
    ),
    "web_form": lambda customer, content: f"Thanks for contacting FlowSync.\n\nNext step: {content}"
}

def normalize_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten incoming message to canonical format."""
    return {
        "channel": msg.get("channel", "unknown"),
        "customer": msg.get("customer_name") or msg.get("customer_email") or msg.get("customer_phone") or "Customer",
        "text": msg.get("message", ""),
        "metadata": {k: v for k, v in msg.items() if k not in {"message", "channel", "customer_name", "customer_email", "customer_phone"}},
    }

def search_docs(query: str) -> str:
    """Find the most relevant doc chunk using simple keyword match. Explicitly handle pricing queries."""
    query_lower = query.lower()
    # 1. Explicit pricing/billing handling
    if re.search(r"pricing|price|cost|plan|subscription.*cost|how much|fee|quote", query_lower):
        return "Pricing questions are always escalated to our human team for an accurate and contractual answer. We'll escalate this immediately."
    # 2. Normal doc search
    best_score = 0
    best_doc = ""
    for title, chunk in PRODUCT_FAQ:
        score = sum(1 for word in query_lower.split() if word in (title + " " + chunk).lower())
        if score > best_score:
            best_score = score
            best_doc = chunk
    return best_doc if best_doc else "I'm sorry, I couldn't find information on that topic in our documentation. If it's about billing, pricing, or legal matters, I'll escalate this to a human team member."

def detect_escalation(text: str, priority: str = "medium") -> bool:
    text = text.lower()
    for pattern in ESCALATION_KEYWORDS:
        if re.search(pattern, text):
            return True
    if priority.lower() == "high":
        return True
    return False

def format_response(content: str, channel: str, customer: str = "Customer") -> str:
    limit = CHANNEL_LIMITS.get(channel, 1500)
    template_fn = CHANNEL_TEMPLATES.get(channel, lambda c, x: x)
    # For WhatsApp, always trim to first short, actionable sentence and remove excess detail
    if channel == 'whatsapp':
        # Restrict to first 1–2 sentences for brevity
        sentences = re.split(r'(?<=[.!?]) +', content)
        formatted = ' '.join(sentences[:2])[:limit]
        if len(formatted) < 120:
            formatted += " 🙂"
        return formatted
    # Normal path for web_form/email
    formatted = template_fn(customer, content)
    if len(formatted) > limit:
        formatted = formatted[:limit-3] + "..."
    return formatted

def handle_customer_message(raw_msg: Dict[str, Any]) -> Dict[str, Any]:
    # Normalize
    msg = normalize_message(raw_msg)
    channel = msg["channel"]
    customer = msg["customer"]
    text = msg["text"]
    prio = raw_msg.get("priority", "medium")
    # Doc search
    doc_response = search_docs(text)
    # Format
    response = format_response(doc_response, channel, customer)
    # Escalation
    escalate = detect_escalation(text, prio)
    return {
        "response": response,
        "escalate": escalate,
        "normalized_message": msg,
    }

# --- Conversation Memory (global in-memory simulation) ---
conversation_memory = {}

def get_customer_id(msg):
    # Prefer email, else phone, else fallback
    return (msg.get("customer_email") or msg.get("customer_phone") or "unknown").lower()

def simple_sentiment(text: str) -> float:
    # Rule-based: strong negative words or exclamation → lower score
    negatives = ["refund", "angry", "ridiculous", "broken", "angry", "terrible", "unacceptable", "sue", "chargeback", "asap", "complaint", "now"]
    lowers = sum(1 for w in negatives if w in text.lower())
    score = 1 - min(1, 0.13 * lowers + text.count("!") * 0.06)
    return max(0.0, min(1.0, score))

def extract_topic(text: str) -> str:
    # Map to basic topic keywords
    if re.search(r"refund|invoice|billing|pricing|charge|vat|tax", text, re.I):
        return "billing"
    if re.search(r"bug|error|broken|issue|crash|fail", text, re.I):
        return "technical"
    if re.search(r"onboard|how\s?to|start|invite", text, re.I):
        return "onboarding"
    if re.search(r"feature|request|suggest", text, re.I):
        return "feedback"
    if re.search(r"delete|erase|remove", text, re.I):
        return "data_deletion"
    return "general"

def update_memory(raw_msg, result, timestamp=None):
    customer_id = get_customer_id(raw_msg)
    mem = conversation_memory.get(customer_id)
    if not mem:
        mem = {
            "customer_id": customer_id,
            "original_channel": raw_msg.get("channel", "unknown"),
            "last_channel": raw_msg.get("channel", "unknown"),
            "open_topic": extract_topic(raw_msg.get("message", "")),
            "topics_discussed": [],
            "history": [],
            "sentiment_trend": [],
            "resolution_status": "pending",
            "channel_switches": 0,
        }
    # If channel differs, record switch
    if mem["last_channel"] != raw_msg.get("channel", "unknown"):
        mem["channel_switches"] += 1
        mem["last_channel"] = raw_msg.get("channel", "unknown")
    # Sentiment
    sentiment = simple_sentiment(raw_msg.get("message", ""))
    mem["sentiment_trend"].append(sentiment)
    if len(mem["sentiment_trend"]) > 7:
        mem["sentiment_trend"] = mem["sentiment_trend"][-7:] # Keep last 7
    # Topic
    topic = extract_topic(raw_msg.get("message", ""))
    if topic and topic not in mem["topics_discussed"]:
        mem["topics_discussed"].append(topic)
    mem["open_topic"] = topic
    # Resolution
    if result["escalate"]:
        mem["resolution_status"] = "escalated"
    elif "solved" in result["response"].lower() or "happy to help" in result["response"].lower():
        mem["resolution_status"] = "solved"
    else:
        mem["resolution_status"] = "pending"
    # History
    mem["history"].append({
        "text": raw_msg.get("message", ""),
        "channel": raw_msg.get("channel", "unknown"),
        "timestamp": timestamp or time.time(),
        "sentiment": sentiment,
        "topic": topic,
        "escalated": result["escalate"]
    })
    conversation_memory[customer_id] = mem
    return mem

def handle_customer_message_with_memory(raw_msg: Dict[str, Any]) -> Dict[str, Any]:
    result = handle_customer_message(raw_msg)
    memory = update_memory(raw_msg, result)
    return {
        **result,
        "memory": memory
    }

# Demo usage
if __name__ == "__main__":
    # WhatsApp refund
    example_ticket = {
        "channel": "whatsapp",
        "customer_name": "Jules",
        "customer_email": "jules@pixelnorth.agency",
        "customer_phone": "+33612000045",
        "category": "billing",
        "priority": "high",
        "message": "hi we got charged twice?? pls refund asap"
    }
    r1 = handle_customer_message_with_memory(example_ticket)
    print("\n--- Agent Demo 1 ---")
    print("RESPONSE:", r1["response"])
    print("ESCALATE:", r1["escalate"])
    print("MEMORY STATE:", r1["memory"])

    # Email follow-up from same customer, now a technical issue
    example_ticket2 = {
        "channel": "email",
        "customer_name": "Jules",
        "customer_email": "jules@pixelnorth.agency",
        "customer_phone": "+33612000045",
        "category": "technical",
        "priority": "medium",
        "message": "Also, timeline view is empty, can you help?"
    }
    r2 = handle_customer_message_with_memory(example_ticket2)
    print("\n--- Agent Demo 2 (Follow up, switched channel) ---")
    print("RESPONSE:", r2["response"])
    print("ESCALATE:", r2["escalate"])
    print("MEMORY STATE:", r2["memory"])
