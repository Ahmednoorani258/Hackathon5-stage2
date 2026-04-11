import asyncio
from production.channels.gmail_handler import GmailHandler

async def main():
    # Use relative path for local development
    handler = GmailHandler("credentials.json")

    # Replace with the actual full name of your topic from GCP
    # Format: projects/YOUR_PROJECT_ID/topics/YOUR_TOPIC_NAME
    topic_name = "projects/crm-hackathon5/topics/gmail-notifications"

    response = await handler.setup_push_notifications(topic_name)
    print("Watch request successful!")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
