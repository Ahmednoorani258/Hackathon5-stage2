# Unofficial WhatsApp API Integration Plan

## 1. The Concept

The unofficial WhatsApp API approach bypasses official providers (like Twilio or Meta's official API) by reverse-engineering the WhatsApp Web protocol. Tools like [`whatsapp-web.js`](https://wwebjs.dev/) or [Baileys](https://github.com/WhiskeySockets/Baileys) operate by launching a headless browser (Puppeteer) or implementing the WebSocket protocol directly to simulate a normal WhatsApp Web session.

To use this, you scan a generated QR code with your mobile WhatsApp app (exactly as you would for WhatsApp Web), which links your personal phone number to the script. The script can then listen for incoming messages and send responses programmatically.

## 2. Risks & Warnings

**IMPORTANT: This approach violates Meta's Terms of Service.**

- **Account Ban Risk**: Meta actively detects and bans numbers using unofficial APIs, especially if they exhibit bot-like behavior (high message volume, rapid responses, spam). If banned, you lose access to your personal WhatsApp account.
- **Instability**: Because these tools reverse-engineer a private API, any update to WhatsApp Web can break the integration, requiring you to update the library and restart the service.
- **Hackathon Rules**: Using this approach in a hackathon often violates the rules regarding supported platforms or stable integration criteria.

## 3. Architecture Design

Since our existing backend is written in Python (FastAPI) and the most robust unofficial WhatsApp libraries are in Node.js/TypeScript, we need a microservice architecture:

1.  **Node.js WhatsApp Bridge**: A small Node.js application running `whatsapp-web.js`.
2.  **Inbound Flow**: The Node.js bridge listens for messages on WhatsApp. When a message is received, it forwards it via HTTP POST to our FastAPI backend (`/webhooks/whatsapp_unofficial`).
3.  **FastAPI Backend**: Processes the message, updates the CRM, and uses the AI agent to generate a response.
4.  **Outbound Flow**: The agent calls a modified `send_response` tool, which makes an HTTP POST request back to the Node.js bridge. The bridge then sends the message to the user on WhatsApp.

```plaintext
[WhatsApp User] <---> [Node.js Bridge (whatsapp-web.js)] <---> HTTP POST <---> [FastAPI Backend]
```

## 4. Step-by-Step Implementation Guide

### Phase 1: Create the Node.js Bridge

1.  Initialize a new Node.js project:
    ```bash
    mkdir whatsapp-bridge && cd whatsapp-bridge
    npm init -y
    npm install whatsapp-web.js qrcode-terminal express body-parser axios
    ```
2.  Create `index.js` to handle QR generation, message listening, and a send endpoint:
    ```javascript
    const { Client, LocalAuth } = require('whatsapp-web.js');
    const qrcode = require('qrcode-terminal');
    const express = require('express');
    const axios = require('axios');
    const bodyParser = require('body-parser');

    const app = express();
    app.use(bodyParser.json());

    // Use LocalAuth to save session data
    const client = new Client({
        authStrategy: new LocalAuth()
    });

    client.on('qr', (qr) => {
        // Generate and scan this code with your phone
        qrcode.generate(qr, {small: true});
        console.log('SCAN THE QR CODE ABOVE WITH WHATSAPP');
    });

    client.on('ready', () => {
        console.log('WhatsApp Client is ready!');
    });

    // Forward incoming messages to FastAPI
    client.on('message', async msg => {
        if(msg.from === 'status@broadcast') return;

        try {
            await axios.post('http://localhost:8000/webhooks/whatsapp_unofficial', {
                From: msg.from, // e.g., '1234567890@c.us'
                Body: msg.body,
                ProfileName: msg._data.notifyName || 'Unknown'
            });
        } catch (error) {
            console.error('Error forwarding message to backend:', error.message);
        }
    });

    // Endpoint for FastAPI to send messages out
    app.post('/send', async (req, res) => {
        const { to, message } = req.body;
        try {
            await client.sendMessage(to, message);
            res.json({ success: true });
        } catch (error) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    client.initialize();
    app.listen(3001, () => console.log('Bridge API listening on port 3001'));
    ```

### Phase 2: Create FastAPI Webhook

In `production/api/main.py` (or a dedicated handler like `channels/whatsapp_unofficial_handler.py`), add the webhook:

```python
from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/webhooks/whatsapp_unofficial")
async def handle_unofficial_whatsapp(request: Request):
    payload = await request.json()
    sender_id = payload.get("From")
    body = payload.get("Body")

    # Clean the sender ID (remove @c.us)
    phone_number = sender_id.split('@')[0] if '@' in sender_id else sender_id

    # 1. Map to customer in CRM
    # 2. Create Ticket
    # 3. Invoke Agent Core with message
    # ... (Integration with existing pipeline)

    return {"status": "received"}
```

### Phase 3: Modify Agent `send_response` Tool

Update the `send_response` tool in your agent configuration to route WhatsApp messages to the Node.js bridge instead of Twilio.

```python
import httpx

async def send_whatsapp_unofficial(phone_number: str, message: str):
    # Format the number correctly for whatsapp-web.js (e.g., adding @c.us)
    target_id = f"{phone_number}@c.us" if not phone_number.endswith('@c.us') else phone_number

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:3001/send",
            json={"to": target_id, "message": message}
        )
        return response.json()
```

## 5. Comparison: Official vs Unofficial

| Feature | Official API (Twilio/Meta) | Unofficial (whatsapp-web.js) |
| :--- | :--- | :--- |
| **Setup Process** | Complex (Business Verification, Approval) | Easy (Just scan a QR code) |
| **Cost** | Per-message pricing + monthly fees | Free |
| **Phone Number** | Requires dedicated, verified business number | Can use any personal number |
| **Stability** | 99.9% Uptime, stable API | Fragile, breaks on WhatsApp Web updates |
| **Ban Risk** | None (if following policies) | Extremely High for automated behavior |
| **Use Case** | Production, Enterprise, Hackathons | Personal projects, prototyping |
