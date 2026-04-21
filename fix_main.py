import re

with open("production/api/main.py", "r") as f:
    content = f.read()

# Replace the body of whatsapp_webhook
old_body = """    try:
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
        )"""

new_body = """    try:
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
                \"\"\"
                INSERT INTO tickets (conversation_id, customer_id, source_channel, category, priority, status)
                VALUES ($1::uuid, $2::uuid, 'whatsapp', 'General Inquiry', 'medium', 'open')
                RETURNING id
                \"\"\",
                conversation_id, customer_id
            )
            
            # Log message
            await conn.execute(
                \"\"\"
                INSERT INTO messages (conversation_id, channel, direction, role, content)
                VALUES ($1::uuid, 'whatsapp', 'inbound', 'user', $2)
                \"\"\",
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
        )"""

if old_body in content:
    content = content.replace(old_body, new_body)
    print("main.py body replaced")
else:
    print("WARNING: Could not find old_body block in main.py")

with open("production/api/main.py", "w") as f:
    f.write(content)
