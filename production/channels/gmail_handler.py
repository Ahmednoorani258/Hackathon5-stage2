import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.cloud import pubsub_v1
import base64
import email
from email.mime.text import MIMEText
from datetime import datetime
import json

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://mail.google.com/']

class GmailHandler:
    def __init__(self, credentials_path: str, token_path: str = 'token.json'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.credentials = self._get_credentials()
        self.service = build('gmail', 'v1', credentials=self.credentials)

    def _get_credentials(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        return creds
        
    async def setup_push_notifications(self, topic_name: str):
        """Set up Gmail push notifications via Pub/Sub."""
        request = {
            'labelIds': ['INBOX'],
            'topicName': topic_name,
            'labelFilterAction': 'include'
        }
        return self.service.users().watch(userId='me', body=request).execute()
    
    async def process_notification(self, pubsub_message: dict) -> list:
        """Process incoming Pub/Sub notification from Gmail."""
        # Use .get() and handle potential nested message key from raw JSON
        history_id = pubsub_message.get('historyId')

        if not history_id:
             history_id = pubsub_message.get('message', {}).get('historyId')

        if not history_id:
            print(f"DEBUG: No historyId found in pubsub_message: {pubsub_message}")
            return []

        print(f"DEBUG: Processing historyId: {history_id}")

        # Get new messages since last history ID
        try:
            history = self.service.users().history().list(
                userId='me',
                startHistoryId=history_id,
                historyTypes=['messageAdded']
            ).execute()
        except Exception as e:
            print(f"DEBUG: Error calling Gmail history API: {e}")
            return []

        messages = []
        # Gmail API might return multiple history records
        for record in history.get('history', []):
            # We ONLY care about new messages added (not label changes etc)
            if 'messagesAdded' in record:
                for msg_added in record['messagesAdded']:
                    msg_id = msg_added['message']['id']

                    # IMPORTANT: Only process if it's in the INBOX and not SENT
                    # This prevents loops where the agent's reply triggers a new notification
                    label_ids = msg_added['message'].get('labelIds', [])
                    if 'INBOX' not in label_ids or 'SENT' in label_ids:
                        print(f"DEBUG: Skipping message {msg_id} (labels: {label_ids})")
                        continue

                    try:
                        print(f"DEBUG: Found new inbound message ID: {msg_id}")
                        message = await self.get_message(msg_id)
                        messages.append(message)
                    except Exception as e:
                        print(f"DEBUG: Could not fetch message {msg_id}: {e}")

        return messages
    
    async def get_message(self, message_id: str) -> dict:
        """Fetch and parse a Gmail message."""
        msg = self.service.users().messages().get(
            userId='me', 
            id=message_id,
            format='full'
        ).execute()
        
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        
        # Extract body
        body = self._extract_body(msg['payload'])
        
        return {
            'channel': 'email',
            'channel_message_id': message_id,
            'customer_email': self._extract_email(headers.get('From', '')),
            'subject': headers.get('Subject', ''),
            'content': body,
            'received_at': datetime.utcnow().isoformat(),
            'thread_id': msg.get('threadId'),
            'metadata': {
                'headers': headers,
                'labels': msg.get('labelIds', [])
            }
        }
    
    def _extract_body(self, payload: dict) -> str:
        """Extract text body from email payload."""
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        
        return ''
    
    def _extract_email(self, from_header: str) -> str:
        """Extract email address from From header."""
        import re
        match = re.search(r'<(.+?)>', from_header)
        return match.group(1) if match else from_header
    
    def send_reply(self, to_email: str, subject: str, body: str, thread_id: str = None) -> dict:
        """Send email reply via Gmail API (synchronous)."""
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        send_request = {'raw': raw}
        if thread_id:
            send_request['threadId'] = thread_id

        result = self.service.users().messages().send(
            userId='me',
            body=send_request
        ).execute()

        print(f"DEBUG: Email sent successfully. Message ID: {result['id']}")

        return {
            'channel_message_id': result['id'],
            'delivery_status': 'sent'
        }