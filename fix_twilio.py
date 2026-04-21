import re

with open("production/channels/whatsapp_handler.py", "r") as f:
    content = f.read()

old_send = """    async def send_message(self, to_phone: str, body: str) -> dict:
        \"\"\"Send WhatsApp message via Twilio.\"\"\"
        # Ensure phone number is in WhatsApp format
        if not to_phone.startswith('whatsapp:'):
            to_phone = f'whatsapp:{to_phone}'
        
        message = self.client.messages.create(
            body=body,
            from_=self.whatsapp_number,
            to=to_phone
        )"""

new_send = """    async def send_message(self, to_phone: str, body: str) -> dict:
        \"\"\"Send WhatsApp message via Twilio.\"\"\"
        # Ensure phone number is in WhatsApp format
        if not to_phone.startswith('whatsapp:'):
            to_phone = f'whatsapp:{to_phone}'
            
        # Ensure from number is in WhatsApp format
        from_phone = self.whatsapp_number
        if from_phone and not from_phone.startswith('whatsapp:'):
            from_phone = f'whatsapp:{from_phone}'
        
        message = self.client.messages.create(
            body=body,
            from_=from_phone,
            to=to_phone
        )"""

if old_send in content:
    content = content.replace(old_send, new_send)
    print("whatsapp_handler.py updated successfully")
else:
    print("WARNING: Could not find old_send block in whatsapp_handler.py")

with open("production/channels/whatsapp_handler.py", "w") as f:
    f.write(content)
