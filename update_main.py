import re

with open("production/api/main.py", "r") as f:
    content = f.read()

whatsapp_setup = """
whatsapp_handler = None
try:
    if os.environ.get('TWILIO_ACCOUNT_SID') and os.environ.get('TWILIO_AUTH_TOKEN'):
        whatsapp_handler = WhatsAppHandler()
        logger.info("Successfully initialized WhatsAppHandler")
    else:
        logger.warning("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN not set; WhatsAppHandler will not be initialized.")
except Exception as e:
    logger.warning(f"Failed to initialize WhatsAppHandler: {e}")
"""

# Insert whatsapp setup after gmail setup
content = re.sub(
    r'(except Exception as e:\n\s+logger\.warning\(f"Failed to initialize GmailHandler: \{e\}"\))',
    r'\1\n' + whatsapp_setup,
    content
)

whatsapp_endpoints = """
@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    if not whatsapp_handler:
        logger.error("WhatsApp integration not configured")
        # Return 200 with empty TwiML anyway so Twilio doesn't retry infinitely
        return Response(content="<Response></Response>", media_type="application/xml")
    
    try:
        form_data = await request.form()
        payload = await whatsapp_handler.process_webhook(form_data)
        
        msg_payload = {
            "channel": "whatsapp",
            "customer_phone": payload.get("customer_phone"),
            "message": payload.get("content"),
            "channel_message_id": payload.get("channel_message_id"),
            "customer_name": payload.get("metadata", {}).get("profile_name", "Customer")
        }
        
        logger.info(f"Received WhatsApp message from {msg_payload['customer_phone']}")
        
        # We need the background_tasks to run handle_customer_message_async
        # However, we must ensure it's executed safely
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
"""

content += "\n" + whatsapp_endpoints

with open("production/api/main.py", "w") as f:
    f.write(content)
