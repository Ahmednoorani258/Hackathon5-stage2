"""Web-form channel handler.

Processing model (current phase):
    Direct async agent invocation via FastAPI BackgroundTasks.
    Kafka event streaming is intentionally deferred; `publish_to_kafka`
    is retained as a no-op hook for architecture parity.
"""

from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, EmailStr, validator
from typing import Any, Optional
import json
import logging
import uuid

from production.database.connection import get_db_pool
from production.agent.customer_success_agent import handle_customer_message_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/support", tags=["support-form"])


class SupportFormSubmission(BaseModel):
    """Support form submission model with validation."""

    name: str
    email: EmailStr
    subject: str
    category: str  # 'general', 'technical', 'billing', 'feedback'
    message: str
    priority: Optional[str] = "medium"
    attachments: Optional[list[str]] = []  # Base64 encoded files or URLs

    @validator("name")
    def name_must_not_be_empty(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @validator("message")
    def message_must_have_content(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("Message must be at least 10 characters")
        return v.strip()

    @validator("category")
    def category_must_be_valid(cls, v):
        valid_categories = ["general", "technical", "billing", "feedback", "bug_report"]
        if v not in valid_categories:
            raise ValueError(f"Category must be one of: {valid_categories}")
        return v


class SupportFormResponse(BaseModel):
    """Response model for form submission."""

    ticket_id: str
    message: str
    estimated_response_time: str


# ---------------------------------------------------------------------------
# Kafka hook (intentional no-op for this phase)
# ---------------------------------------------------------------------------

async def publish_to_kafka(topic: str, message_data: dict[str, Any]) -> None:
    """Kafka hook placeholder for architecture parity.

    Kafka event streaming is intentionally deferred for the current
    deployment phase.  This stub is kept so the code path mirrors the
    target Specialization-phase architecture without requiring a running
    Kafka broker.
    """
    logger.info(
        "[web_form] Kafka publish hook (noop). topic=%s channel=%s channel_message_id=%s",
        topic,
        message_data.get("channel"),
        message_data.get("channel_message_id"),
    )


# ---------------------------------------------------------------------------
# Customer resolution
# ---------------------------------------------------------------------------

async def _resolve_customer_id(conn, email: str, name: str) -> str:
    """Find or create a customer record by email, returning the UUID."""
    customer_id = await conn.fetchval("SELECT id FROM customers WHERE email = $1", email)
    if customer_id:
        await conn.execute(
            "UPDATE customers SET name = COALESCE(name, $2) WHERE id = $1::uuid",
            customer_id,
            name,
        )
        logger.debug("[web_form] Resolved existing customer id=%s for email=%s", customer_id, email)
        return str(customer_id)

    customer_id = await conn.fetchval(
        "INSERT INTO customers (email, name) VALUES ($1, $2) RETURNING id",
        email,
        name,
    )
    logger.info("[web_form] Created new customer id=%s for email=%s", customer_id, email)
    return str(customer_id)


# ---------------------------------------------------------------------------
# Ticket / message persistence
# ---------------------------------------------------------------------------

async def create_ticket_record(ticket_id: str, message_data: dict[str, Any]) -> None:
    """Persist customer, conversation, ticket, and inbound message rows.

    This function MUST complete before the agent background task runs so
    the ticket-first invariant is always satisfied.
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        customer_id = await _resolve_customer_id(
            conn,
            message_data["customer_email"],
            message_data.get("customer_name") or "Customer",
        )

        conversation_metadata = {
            "subject": message_data.get("subject"),
            "category": message_data.get("category"),
            "priority": message_data.get("priority"),
        }
        # asyncpg expects a JSON string for jsonb parameters in some contexts
        conversation_id = await conn.fetchval(
            """
            INSERT INTO conversations (customer_id, initial_channel, metadata)
            VALUES ($1::uuid, 'web_form', $2::jsonb)
            RETURNING id
            """,
            customer_id,
            json.dumps(conversation_metadata),
        )

        logger.debug(
            "[web_form] Conversation created. conversation_id=%s metadata=%s",
            conversation_id,
            conversation_metadata,
        )

        await conn.execute(
            """
            INSERT INTO tickets (id, conversation_id, customer_id, source_channel, category, priority, status)
            VALUES ($1::uuid, $2::uuid, $3::uuid, 'web_form', $4, $5, 'open')
            """,
            ticket_id,
            conversation_id,
            customer_id,
            message_data.get("category"),
            message_data.get("priority") or "medium",
        )

        await conn.execute(
            """
            INSERT INTO messages (
                conversation_id,
                channel,
                direction,
                role,
                content,
                channel_message_id,
                delivery_status
            )
            VALUES ($1::uuid, 'web_form', 'inbound', 'customer', $2, $3, 'delivered')
            """,
            conversation_id,
            message_data.get("content") or "",
            message_data.get("channel_message_id"),
        )

        logger.info(
            "[web_form] Ticket persisted. ticket_id=%s customer_id=%s conversation_id=%s channel=web_form",
            ticket_id,
            customer_id,
            conversation_id,
        )


# ---------------------------------------------------------------------------
# Ticket lookup
# ---------------------------------------------------------------------------

async def get_ticket_by_id(ticket_id: str) -> Optional[dict[str, Any]]:
    """Return ticket status and chronological messages, or None."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        ticket = await conn.fetchrow(
            """
            SELECT t.id, t.status, t.created_at, c.id AS conversation_id
            FROM tickets t
            JOIN conversations c ON c.id = t.conversation_id
            WHERE t.id = $1::uuid
            """,
            ticket_id,
        )

        if not ticket:
            return None

        message_rows = await conn.fetch(
            """
            SELECT channel, direction, role, content, created_at, channel_message_id, delivery_status
            FROM messages
            WHERE conversation_id = $1::uuid
            ORDER BY created_at ASC
            """,
            ticket["conversation_id"],
        )

        messages = [
            {
                "channel": row["channel"],
                "direction": row["direction"],
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "channel_message_id": row["channel_message_id"],
                "delivery_status": row["delivery_status"],
            }
            for row in message_rows
        ]

        last_updated = ticket["created_at"]
        if message_rows:
            last_updated = max(row["created_at"] for row in message_rows if row["created_at"])

        return {
            "status": ticket["status"],
            "messages": messages,
            "created_at": ticket["created_at"].isoformat() if ticket["created_at"] else None,
            "last_updated": last_updated.isoformat() if last_updated else None,
        }


# ---------------------------------------------------------------------------
# Agent background task wrapper
# ---------------------------------------------------------------------------

async def _run_agent_in_background(agent_payload: dict[str, Any]) -> None:
    """Wrapper that invokes the agent and logs the outcome."""
    ticket_id = agent_payload.get("channel_message_id", "unknown")
    logger.error("[web_form] STARTING BACKGROUND AGENT TASK. ticket_id=%s", ticket_id)
    try:
        result = await handle_customer_message_async(agent_payload)
        status = result.get("status", "unknown")
        logger.error(
            "[web_form] Agent task completed. ticket_id=%s status=%s result=%s",
            ticket_id,
            status,
            result
        )
    except Exception as e:
        logger.exception(
            "[web_form] Agent task failed. ticket_id=%s error=%s",
            ticket_id,
            str(e)
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/submit", response_model=SupportFormResponse)
async def submit_support_form(submission: SupportFormSubmission, background_tasks: BackgroundTasks):
    """Handle support form submission.

    Pipeline (direct async — Kafka intentionally deferred):
    1. Validate the submission (Pydantic).
    2. Persist customer + conversation + ticket + inbound message (ticket-first).
    3. Queue direct async agent processing via BackgroundTasks.
    4. Return ticket_id confirmation to the caller immediately.
    """
    ticket_id = str(uuid.uuid4())
    logger.info(
        "[web_form] Submission accepted. ticket_id=%s email=%s category=%s priority=%s",
        ticket_id,
        submission.email,
        submission.category,
        submission.priority,
    )

    message_data = {
        "channel": "web_form",
        "channel_message_id": ticket_id,
        "customer_email": submission.email,
        "customer_name": submission.name,
        "subject": submission.subject,
        "content": submission.message,
        "category": submission.category,
        "priority": submission.priority,
        "received_at": datetime.utcnow().isoformat(),
        "metadata": {
            "form_version": "1.0",
            "attachments": submission.attachments,
        },
    }

    # No-op Kafka hook retained for architecture parity
    await publish_to_kafka("fte.tickets.incoming", message_data)

    # Ticket-first: persist BEFORE queuing the agent
    await create_ticket_record(ticket_id, message_data)

    agent_payload = {
        "channel": "web_form",
        "customer_email": submission.email,
        "customer_name": submission.name,
        "subject": submission.subject,
        "message": submission.message,
        "category": submission.category,
        "priority": submission.priority or "medium",
        "channel_message_id": ticket_id,
    }
    background_tasks.add_task(_run_agent_in_background, agent_payload)

    logger.info("[web_form] Response returned to client. ticket_id=%s", ticket_id)

    return SupportFormResponse(
        ticket_id=ticket_id,
        message="Thank you for contacting us! Our AI assistant will respond shortly.",
        estimated_response_time="Usually within 5 minutes",
    )


@router.get("/ticket/{ticket_id}")
async def get_ticket_status(ticket_id: str):
    """Get status and conversation history for a ticket."""
    ticket = await get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {
        "ticket_id": ticket_id,
        "status": ticket["status"],
        "messages": ticket["messages"],
        "created_at": ticket["created_at"],
        "last_updated": ticket["last_updated"],
    }
