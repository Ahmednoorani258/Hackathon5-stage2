from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.cloud import pubsub_v1
import base64
import email
from email.mime.text import MIMEText
from datetime import datetime
import json

class GmailHandler:
    def __init__(self, credentials_path: str):
        self.credentials = Credentials.from_authorized_user_file(credentials_path)
        self.service = build('gmail', 'v1', credentials=self.credentials)
        
    async def setup_push_notifications(self, topic_name: str):
        """Set up Gmail push notifications via Pub/Sub."""
        request = {
            'labelIds': ['INBOX'],
            'topicName': topic_name,
            'labelFilterAction': 'include'
        }
        return self.service.users().watch(userId='me', body=request).execute()
    
    async def process_notification(self, pubsub_message: dict) -> dict:
        """Process incoming Pub/Sub notification from Gmail."""
        history_id = pubsub_message.get('historyId')
        
        # Get new messages since last history ID
        history = self.service.users().history().list(
            userId='me',
            startHistoryId=history_id,
            historyTypes=['messageAdded']
        ).execute()
        
        messages = []
        for record in history.get('history', []):
            for msg_added in record.get('messagesAdded', []):
                msg_id = msg_added['message']['id']
                message = await self.get_message(msg_id)
                messages.append(message)
        
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
    
    async def send_reply(self, to_email: str, subject: str, body: str, thread_id: str = None) -> dict:
        """Send email reply."""
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
        
        return {
            'channel_message_id': result['id'],
            'delivery_status': 'sent'
        }