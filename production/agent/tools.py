from agents import function_tool
from pydantic import BaseModel
from typing import Optional
import logging

from production.database.connection import get_db_pool
from production.agent.embeddings import generate_embedding

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# 1. Search Knowledge Base
# -----------------------------------------------------------------------------
class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge base search."""
    query: str
    max_results: int = 5
    category: Optional[str] = None

@function_tool
async def search_knowledge_base(input: KnowledgeSearchInput) -> str:
    """Search product documentation for relevant information.

    Use this when the customer asks questions about product features,
    how to use something, or needs technical information.

    Args:
        input: Search parameters including query and optional filters

    Returns:
        Formatted search results with relevance scores
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            embedding = await generate_embedding(input.query)

            # Note: Assuming 'embedding' is a JSON string or appropriate vector type for asyncpg
            results = await conn.fetch("""
                SELECT title, content, category,
                       1 - (embedding <=> $1::vector) as similarity
                FROM knowledge_base
                WHERE ($2::text IS NULL OR category = $2)
                ORDER BY embedding <=> $1::vector
                LIMIT $3
            """, embedding, input.category, input.max_results)

            if not results:
                return "No relevant documentation found. Consider escalating to human support."

            formatted = []
            for r in results:
                formatted.append(f"**{r['title']}** (relevance: {r['similarity']:.2f})\\n{r['content'][:500]}")

            return "\\n\\n---\\n\\n".join(formatted)

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        return "Knowledge base temporarily unavailable. Please try again or escalate."

# -----------------------------------------------------------------------------
# 2. Create Ticket
# -----------------------------------------------------------------------------
class CreateTicketInput(BaseModel):
    """Input schema for creating a support ticket."""
    customer_id: str
    source_channel: str
    category: str
    priority: str
    notes: Optional[str] = None

@function_tool
async def create_ticket(input: CreateTicketInput) -> str:
    """Create a new support ticket in the CRM.

    EVERY INTAKE MUST create a new ticket before any agent response.

    Args:
        input: Details for the new ticket

    Returns:
        The ID of the newly created ticket, or an error message.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            ticket_id = await conn.fetchval("""
                INSERT INTO tickets (customer_id, source_channel, category, priority, status, notes)
                VALUES ($1, $2, $3, $4, 'open', $5)
                RETURNING id
            """, input.customer_id, input.source_channel, input.category, input.priority, input.notes)

            return f"Ticket created successfully. Ticket ID: {ticket_id}"

    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        return "Failed to create ticket."

# -----------------------------------------------------------------------------
# 3. Get Customer History
# -----------------------------------------------------------------------------
class GetCustomerHistoryInput(BaseModel):
    """Input schema for retrieving customer history."""
    customer_id: str

@function_tool
async def get_customer_history(input: GetCustomerHistoryInput) -> str:
    """Retrieve the cross-channel interaction summary for a customer.

    Always check this before responding to get context on the customer's previous issues.

    Args:
        input: The customer ID

    Returns:
        A summary of the customer's recent conversations and tickets.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            conversations = await conn.fetch("""
                SELECT initial_channel, started_at, status, sentiment_score
                FROM conversations
                WHERE customer_id = $1
                ORDER BY started_at DESC
                LIMIT 5
            """, input.customer_id)

            if not conversations:
                return "No previous interaction history found for this customer."

            formatted = ["Recent Conversations:"]
            for conv in conversations:
                formatted.append(f"- Channel: {conv['initial_channel']}, Date: {conv['started_at']}, Status: {conv['status']}, Sentiment: {conv['sentiment_score']}")

            return "\\n".join(formatted)

    except Exception as e:
        logger.error(f"Failed to fetch customer history: {e}")
        return "Failed to fetch customer history."

# -----------------------------------------------------------------------------
# 4. Escalate to Human
# -----------------------------------------------------------------------------
class EscalateToHumanInput(BaseModel):
    """Input schema for escalating a ticket to human support."""
    ticket_id: int
    reason: str

@function_tool
async def escalate_to_human(input: EscalateToHumanInput) -> str:
    """Escalate a ticket to a human representative.

    Use this when:
    - Customer asks about pricing, refund, legal, competitor.
    - Sentiment < 0.3 OR profanity/hate detected.
    - Customer explicitly requests human.
    - WhatsApp messages "human/agent/representative".
    - AI can't resolve after 2 failed knowledge base searches.

    Args:
        input: Ticket ID and the reason for escalation

    Returns:
        Status message about the escalation.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Update the ticket status to 'escalated'
            await conn.execute("""
                UPDATE tickets
                SET status = 'escalated', notes = CONCAT(notes, '\\nEscalation Reason: ', $2::text)
                WHERE id = $1
            """, input.ticket_id, input.reason)

            return f"Ticket {input.ticket_id} has been escalated to a human. Reason: {input.reason}"

    except Exception as e:
        logger.error(f"Failed to escalate ticket: {e}")
        return "Failed to escalate ticket."

# -----------------------------------------------------------------------------
# 5. Send Response
# -----------------------------------------------------------------------------
class SendResponseInput(BaseModel):
    """Input schema for sending a response to a customer."""
    ticket_id: int
    message: str
    channel: str

@function_tool
async def send_response(input: SendResponseInput) -> str:
    """Send an outbound response to the customer via the specified channel.

    EVERY REPLY MUST USE THIS TOOL. Ensure the message formatting matches the
    channel's requirements:
    - Gmail: Formal, detailed (max 500 words)
    - WhatsApp: Conversational, concise (max 160 chars preferred)
    - Web Form: Semi-formal (max 300 words)

    Args:
        input: Ticket ID, response message, and the target channel

    Returns:
        Status message about the response delivery.
    """
    try:
        # In a real implementation, this would route to the specific channel's
        # outbound API (e.g., Gmail API, Twilio API).
        logger.info(f"Sending response for ticket {input.ticket_id} via {input.channel}: {input.message}")

        # We would also log this message in the messages table
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get conversation_id for this ticket
            conversation_id = await conn.fetchval("""
                SELECT conversation_id FROM tickets WHERE id = $1
            """, input.ticket_id)

            if conversation_id:
                await conn.execute("""
                    INSERT INTO messages (conversation_id, channel, direction, role, content)
                    VALUES ($1, $2, 'outbound', 'agent', $3)
                """, conversation_id, input.channel, input.message)

        return f"Response sent successfully via {input.channel}."

    except Exception as e:
        logger.error(f"Failed to send response: {e}")
        return "Failed to send response."
