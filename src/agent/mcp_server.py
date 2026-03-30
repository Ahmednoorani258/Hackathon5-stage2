from enum import Enum
from mcp.server import Server
from mcp.types import Tool, TextContent
import uuid

from core_loop import (
    conversation_memory, search_docs, format_response, get_customer_id, update_memory
)

# Channel enum
def _channel_values():
    return ["email", "whatsapp", "web_form"]

class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"

server = Server("customer-success-fte")

tickets_db = {}
escalations_db = {}

@server.tool("search_knowledge_base")
async def search_kb(query: str) -> str:
    """Search product documentation for relevant information."""
    return search_docs(query)

@server.tool("create_ticket")
async def create_ticket(
    customer_id: str,
    issue: str,
    priority: str,
    channel: Channel
) -> str:
    """Create a support ticket in the system with channel tracking."""
    ticket_id = str(uuid.uuid4())
    tickets_db[ticket_id] = dict(
        ticket_id=ticket_id,
        customer_id=customer_id,
        issue=issue,
        priority=priority,
        channel=channel.value if isinstance(channel, Channel) else channel,
        status="pending" if priority != "high" else "escalated",
        history=[issue],
    )
    return ticket_id

@server.tool("get_customer_history")
async def get_customer_history(customer_id: str) -> str:
    """Get customer's interaction history across ALL channels."""
    mem = conversation_memory.get(customer_id)
    if not mem:
        return f"No history found for customer_id: {customer_id}"
    out = [f"Topics discussed: {', '.join(mem['topics_discussed'])}",
           f"Resolution status: {mem['resolution_status']}",
           f"Original channel: {mem['original_channel']}",
           f"Channels switched: {mem['channel_switches']}"]
    out.append("Recent messages:")
    for h in mem["history"][-5:]:
        out.append(f"[{h['channel']}] Sentiment: {h['sentiment']:.2f} | Topic: {h['topic']} | {h['text']}")
    return "\n".join(out)

@server.tool("escalate_to_human")
async def escalate_to_human(ticket_id: str, reason: str) -> str:
    """Escalate a support ticket to a human team with reason."""
    escalation_id = str(uuid.uuid4())
    escalations_db[escalation_id] = {
        "escalation_id": escalation_id,
        "ticket_id": ticket_id,
        "reason": reason,
        "status": "open"
    }
    t = tickets_db.get(ticket_id)
    if t:
        t["status"] = "escalated"
    return escalation_id

@server.tool("send_response")
async def send_response(
    ticket_id: str,
    message: str,
    channel: Channel
) -> str:
    """Send response via the appropriate channel."""
    t = tickets_db.get(ticket_id)
    if t:
        response = format_response(message, channel.value if isinstance(channel, Channel) else channel)
        t.setdefault("responses", []).append(response)
        t["status"] = "solved"
        return f"[SENT to {channel.value}] {response}"
    return f"Ticket ID {ticket_id} not found. Unable to send."

if __name__ == "__main__":
    server.run()
