"""Channel-specific response formatters.

Implement helpers to format messages for Email, WhatsApp, and Web Form.
"""

def format_for_email(text, ticket_id=None):
    greeting = "Dear Customer,\n\n"
    signature = "\n\nBest regards,\nTechCorp AI Support Team"
    footer = f"\n---\nTicket Reference: {ticket_id}" if ticket_id else ""
    return greeting + text + signature + footer


def format_for_whatsapp(text):
    # Keep concise; truncate if necessary
    max_len = 300
    if len(text) > max_len:
        return text[:max_len-3] + '...'
    return text


def format_for_web(text):
    return text + "\n\n---\nNeed more help? Reply to this message or visit our support portal."
