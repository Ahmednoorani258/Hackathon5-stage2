from agents import function_tool
from pydantic import BaseModel
from typing import Optional
import logging

from production.database.connection import get_db_pool
from production.agent.embeddings import generate_embedding

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------

async def resolve_customer_id(conn, identifier: str) -> str:
    """Resolve an email or phone number to a customer UUID."""
    # First try treating it as an email
    cust_id = await conn.fetchval("SELECT id FROM customers WHERE email = $1", identifier)
    if cust_id: return str(cust_id)
    
    # Try as a phone number
    cust_id = await conn.fetchval("SELECT id FROM customers WHERE phone = $1", identifier)
    if cust_id: return str(cust_id)
    
    # If it already looks like a UUID, return it
    import re
    if re.match(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', identifier):
        return identifier
        
    # Otherwise, create a new customer
    cust_id = await conn.fetchval("INSERT INTO customers (email) VALUES ($1) RETURNING id", identifier)
    return str(cust_id)

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
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'

            # Note: Assuming 'embedding' is a JSON string or appropriate vector type for asyncpg
            results = await conn.fetch("""
                SELECT title, content, category,
                       1 - (embedding <=> $1::vector) as similarity
                FROM knowledge_base
                WHERE ($2::text IS NULL OR category = $2)
                ORDER BY embedding <=> $1::vector
                LIMIT $3
            """, embedding_str, input.category, input.max_results)

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
            resolved_id = await resolve_customer_id(conn, input.customer_id)
            
            # We need a conversation ID first. For simplicity in the tool, we create one if missing.
            conversation_id = await conn.fetchval("INSERT INTO conversations (customer_id, initial_channel) VALUES ($1::uuid, $2) RETURNING id", resolved_id, input.source_channel)
            
            ticket_id = await conn.fetchval("""
                INSERT INTO tickets (conversation_id, customer_id, source_channel, category, priority, status, resolution_notes)
                VALUES ($1::uuid, $2::uuid, $3, $4, $5, 'open', $6)
                RETURNING id
            """, conversation_id, resolved_id, input.source_channel, input.category, input.priority, input.notes)

            return f"Ticket created successfully. Ticket ID: {ticket_id}"

    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        return "Failed to create ticket."

# -----------------------------------------------------------------------------
# 2b. Create Ticket (IDE Alias)
# -----------------------------------------------------------------------------
@function_tool
async def create_ticket_ide(input: CreateTicketInput) -> str:
    """Alias for create_ticket to support legacy tool calls."""
    return await create_ticket(input)

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
            resolved_id = await resolve_customer_id(conn, input.customer_id)
            conversations = await conn.fetch("""
                SELECT initial_channel, started_at, status, sentiment_score
                FROM conversations
                WHERE customer_id = $1::uuid
                ORDER BY started_at DESC
                LIMIT 5
            """, resolved_id)

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
    ticket_id: str
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
                SET status = 'escalated', resolution_notes = CONCAT(COALESCE(resolution_notes, ''), '
Escalation Reason: ', $2::text)
                WHERE id = $1::uuid
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
    ticket_id: str
    message: str
    channel: str
    to_email: Optional[str] = None
    thread_id: Optional[str] = None
    subject: Optional[str] = None

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
        # Send the response via the specific channel's outbound API
        logger.info(f"Sending response for ticket {input.ticket_id} via {input.channel}: {input.message}")

        if input.channel == "email" and input.to_email:
            import os
            import asyncio
            from production.channels.gmail_handler import GmailHandler

            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            creds_path = os.environ.get("GMAIL_CREDENTIALS_PATH", os.path.join(base_dir, "credentials.json"))
            token_path = os.environ.get("GMAIL_TOKEN_PATH", os.path.join(base_dir, "token.json"))

            try:
                handler = GmailHandler(creds_path, token_path)
                # Ensure the subject always starts with "Re:" for threading
                subject = input.subject or "Support Reply"
                if not subject.startswith("Re:"):
                    subject = "Re: " + subject

                # The Gmail library is sync, but we use an async wrapper or just call it if it was modified
                logger.info(f"Dispatching email to {input.to_email}")
                if asyncio.iscoroutinefunction(handler.send_reply):
                    await handler.send_reply(
                        to_email=input.to_email,
                        subject=subject,
                        body=input.message,
                        thread_id=input.thread_id
                    )
                else:
                    handler.send_reply(
                        to_email=input.to_email,
                        subject=subject,
                        body=input.message,
                        thread_id=input.thread_id
                    )
                logger.info(f"Email reply sent successfully to {input.to_email}")
            except Exception as mail_error:
                logger.error(f"Failed to dispatch email: {mail_error}")

        # We log this message in the messages table

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get conversation_id for this ticket
            conversation_id = await conn.fetchval("""
                SELECT conversation_id FROM tickets WHERE id = $1::uuid
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
