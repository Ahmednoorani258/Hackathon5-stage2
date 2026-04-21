"""FastAPI app for channel endpoints and health checks."""

from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import base64
import logging
import os

from production.channels.gmail_handler import GmailHandler
from production.channels.whatsapp_handler import WhatsAppHandler
from production.channels.web_form_handler import router as web_form_router
from production.agent.customer_success_agent import handle_customer_message_async
from production.database.connection import get_db_pool

# Configure logging to use uvicorn's logger so logs show in terminal
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Customer Success FTE API")

# CORS — allow the Next.js frontend (dev and deployed) to call the API
_allowed_origins = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(web_form_router, prefix="/api")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GMAIL_CREDENTIALS_PATH = os.environ.get("GMAIL_CREDENTIALS_PATH", os.path.join(BASE_DIR, "credentials.json"))
GMAIL_TOKEN_PATH = os.environ.get("GMAIL_TOKEN_PATH", os.path.join(BASE_DIR, "token.json"))
HISTORY_ID_FILE = os.path.join(BASE_DIR, "last_history_id.txt")

gmail_handler = None

def get_last_history_id():
    if os.path.exists(HISTORY_ID_FILE):
        with open(HISTORY_ID_FILE, 'r') as f:
            return f.read().strip()
    return None

def save_last_history_id(history_id):
    with open(HISTORY_ID_FILE, 'w') as f:
        f.write(str(history_id))

try:
    if os.path.exists(GMAIL_CREDENTIALS_PATH):
        if os.path.exists(GMAIL_TOKEN_PATH):
            gmail_handler = GmailHandler(GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH)
            logger.info(f"Successfully initialized GmailHandler using {GMAIL_TOKEN_PATH}")
except Exception as e:
    logger.warning(f"Failed to initialize GmailHandler: {e}")

whatsapp_handler = None
try:
    if os.environ.get('TWILIO_ACCOUNT_SID') and os.environ.get('TWILIO_AUTH_TOKEN'):
        whatsapp_handler = WhatsAppHandler()
        logger.info("Successfully initialized WhatsAppHandler")
    else:
        logger.warning("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN not set; WhatsAppHandler will not be initialized.")
except Exception as e:
    logger.warning(f"Failed to initialize WhatsAppHandler: {e}")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhooks/gmail", status_code=204)
async def gmail_webhook(request: Request):
    try:
        data = await request.json()
        message_data = data.get("message", {}).get("data")
        if not message_data:
            return Response(status_code=204)
            
        decoded_data = base64.b64decode(message_data).decode("utf-8")
        pubsub_message = json.loads(decoded_data)
        new_history_id = pubsub_message.get('historyId')
        
        if gmail_handler:
            last_id = get_last_history_id()

            # On first notification after restart, initialize baseline only.
            # This prevents massive replay of old inbox history.
            if not last_id:
                save_last_history_id(new_history_id)
                logger.info(f"Initialized Gmail history baseline at {new_history_id}; skipping replay on first event")
                return Response(status_code=204)

            # Ignore out-of-order or duplicate notifications
            try:
                if int(new_history_id) <= int(last_id):
                    logger.info(f"Ignoring stale/duplicate Gmail notification. New: {new_history_id}, Last: {last_id}")
                    return Response(status_code=204)
            except Exception:
                pass

            save_last_history_id(new_history_id)

            logger.info(f"Processing Gmail notification. History ID: {new_history_id} (Last: {last_id})")
            emails = await gmail_handler.process_notification({"historyId": last_id})
            logger.info(f"Found {len(emails)} candidate inbound emails from history delta")

            skip_domains = {
                "alerts.linkedin.com",
                "e.linkedin.com",
                "linkedin.com",
                "em.indeed.com",
                "indeed.com",
                "notifications.github.com",
                "no-reply.atlassian.com",
                "mailer-daemon.googlemail.com",
                "mailer-daemon.gmail.com",
            }
            skip_keywords = {
                "noreply",
                "no-reply",
                "do-not-reply",
                "donotreply",
                "automated",
                "notification",
                "notifications",
                "alert",
                "digest",
                "newsletter",
                "jobalert",
                "job-alert",
                "linkedin",
                "indeed",
                "glassdoor",
            }

            for email_data in emails:
                sender = (email_data.get("customer_email") or "").strip().lower()
                sender_domain = sender.split("@")[-1] if "@" in sender else ""

                if sender_domain in skip_domains or any(k in sender for k in skip_keywords):
                    logger.info(
                        "Skipped automated inbound email from sender=%s domain=%s",
                        sender,
                        sender_domain,
                    )
                    continue

                if not sender:
                    logger.info("Skipped inbound email with empty sender")
                    continue

                logger.info("Accepted inbound customer email from sender=%s domain=%s", sender, sender_domain)


                msg_payload = {
                    "channel": "email",
                    "customer_email": sender,
                    "subject": email_data.get("subject"),
                    "message": email_data.get("content"),
                    "thread_id": email_data.get("thread_id"),
                    "channel_message_id": email_data.get("channel_message_id")
                }
                
                try:
                    # Run agent directly in current async loop to avoid cross-loop asyncpg errors
                    result = await handle_customer_message_async(msg_payload)
                    logger.info(f"Agent processing result: {result.get('status')}")
                except Exception as e:
                    logger.error(f"Error in agent processing: {e}")

        return Response(status_code=204)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response(status_code=204)


@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    if not whatsapp_handler:
        logger.error("WhatsApp integration not configured")
        # Return 200 with empty TwiML anyway so Twilio doesn't retry infinitely
        return Response(content="<Response></Response>", media_type="application/xml")
    
    try:
        form_data = await request.form()
        payload = await whatsapp_handler.process_webhook(form_data)
        
        customer_phone = payload.get("customer_phone")
        content_text = payload.get("content")
        profile_name = payload.get("metadata", {}).get("profile_name", "Customer")

        # 1. Ticket-First Persistence logic
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Resolve customer - check both phone and email columns for the identifier
            customer_id = await conn.fetchval("SELECT id FROM customers WHERE phone = $1 OR email = $1", customer_phone)
            if not customer_id:
                customer_id = await conn.fetchval(
                    "INSERT INTO customers (phone, name) VALUES ($1, $2) RETURNING id",
                    customer_phone, profile_name
                )
            
            # Create conversation
            conversation_id = await conn.fetchval(
                "INSERT INTO conversations (customer_id, initial_channel) VALUES ($1::uuid, 'whatsapp') RETURNING id",
                customer_id
            )
            
            # Create ticket
            ticket_id = await conn.fetchval(
                """
                INSERT INTO tickets (conversation_id, customer_id, source_channel, category, priority, status)
                VALUES ($1::uuid, $2::uuid, 'whatsapp', 'General Inquiry', 'medium', 'open')
                RETURNING id
                """,
                conversation_id, customer_id
            )
            
            # Log message
            await conn.execute(
                """
                INSERT INTO messages (conversation_id, channel, direction, role, content)
                VALUES ($1::uuid, 'whatsapp', 'inbound', 'user', $2)
                """,
                conversation_id, content_text
            )

        msg_payload = {
            "channel": "whatsapp",
            "customer_phone": customer_phone,
            "message": content_text,
            "channel_message_id": payload.get("channel_message_id"),
            "customer_name": profile_name,
            "ticket_id": str(ticket_id)
        }
        
        logger.info(f"Received WhatsApp message from {customer_phone}, created ticket {ticket_id}")
        
        # Hand off to agent
        background_tasks.add_task(
            handle_customer_message_async_task,
            msg_payload
        )
        
    except Exception as e:
        logger.error(f"WhatsApp Webhook error: {e}")

    # Return valid TwiML
    return Response(content="<Response></Response>", media_type="application/xml")

@app.post("/webhooks/whatsapp/status")
async def whatsapp_status(request: Request):
    try:
        form_data = await request.form()
        status = form_data.get('MessageStatus')
        sid = form_data.get('MessageSid')
        logger.info(f"WhatsApp message {sid} status update: {status}")
    except Exception as e:
        logger.error(f"WhatsApp Status Webhook error: {e}")
    return Response(content="<Response></Response>", media_type="application/xml")

# Wrapper for background tasks to handle async properly
async def handle_customer_message_async_task(msg_payload):
    try:
        await handle_customer_message_async(msg_payload)
    except Exception as e:
        logger.error(f"Error in WhatsApp agent processing: {e}")
