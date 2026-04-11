"""FastAPI app for channel endpoints and health checks."""

from fastapi import FastAPI, Request, Response
import json
import base64
import logging
import os

from production.channels.gmail_handler import GmailHandler
from production.channels.web_form_handler import router as web_form_router
from production.agent.customer_success_agent import handle_customer_message_async

# Configure logging to use uvicorn's logger so logs show in terminal
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Customer Success FTE API")
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

            search_id = last_id
            save_last_history_id(new_history_id)

            logger.info(f"Processing Gmail notification. History ID: {new_history_id} (Last: {last_id})")
            emails = await gmail_handler.process_notification({"historyId": search_id})
            logger.info(f"Found {len(emails)} candidate inbound emails from history delta")
            
            for email_data in emails:
                sender = email_data.get("customer_email", "").lower()
                # Skip automated emails and job alerts
                skip_keywords = [
                    "noreply", "no-reply", "automated", "notifications",
                    "glassdoor", "indeed", "linkedin", "jobalert", "digest"
                ]
                if any(x in sender for x in skip_keywords):
                    logger.info(f"Skipping automated email/alert from {sender}")
                    continue

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
