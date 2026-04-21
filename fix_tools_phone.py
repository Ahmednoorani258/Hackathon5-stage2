import re

with open("production/agent/tools.py", "r") as f:
    content = f.read()

old_query = """                    customer_data = await conn.fetchrow(\"\"\"
                        SELECT c.phone, t.customer_id
                        FROM tickets t
                        LEFT JOIN customers c ON t.customer_id = c.id
                        WHERE t.id = $1::uuid
                    \"\"\", input.ticket_id)

                customer_phone = None
                if customer_data:
                    customer_phone = customer_data['phone'] or customer_data['customer_id']"""

new_query = """                    customer_data = await conn.fetchrow(\"\"\"
                        SELECT c.phone, c.email, t.customer_id
                        FROM tickets t
                        LEFT JOIN customers c ON t.customer_id = c.id
                        WHERE t.id = $1::uuid
                    \"\"\", input.ticket_id)

                customer_phone = None
                if customer_data:
                    # In case the phone number was accidentally stored in the email column due to old bugs
                    customer_phone = customer_data['phone'] or customer_data['email']
                    
                    # Ensure it's not a UUID
                    if customer_phone and '-' in customer_phone and len(customer_phone) > 30:
                        customer_phone = None
                        
                    # Fallback to customer_id if somehow we still don't have it (though this will fail Twilio)
                    if not customer_phone:
                        customer_phone = customer_data['customer_id']"""

if old_query in content:
    content = content.replace(old_query, new_query)
    print("tools.py updated to handle phone in email column")
else:
    print("WARNING: Could not find old_query block in tools.py")

with open("production/agent/tools.py", "w") as f:
    f.write(content)
