import logging
import asyncio
from typing import Dict, Any

from agents import Agent, Runner
from production.agent.setup_config import config

from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from production.agent.tools import (
    search_knowledge_base,
    create_ticket,
    create_ticket_ide,
    get_customer_history,
    get_customer_history_ide,
    escalate_to_human,
    send_response
)

logger = logging.getLogger(__name__)

def create_customer_success_agent() -> Agent:
    """Create the Customer Success Digital FTE using the OpenAI Agents SDK."""
    return Agent(
        name="FlowSync Customer Success Agent",
        instructions=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
        tools=[
            create_ticket,
            create_ticket_ide,
            get_customer_history,
            get_customer_history_ide,
            search_knowledge_base,
            send_response,
            escalate_to_human
        ]
    )

async def handle_customer_message_async(msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an incoming customer message using the OpenAI Agents SDK.

    Args:
        msg: Incoming message payload with fields like:
             channel, customer_name, customer_email, customer_phone, message, priority
    """
    channel = msg.get("channel", "unknown")
    customer_name = msg.get("customer_name") or msg.get("customer_email") or msg.get("customer_phone") or "Customer"
    text = msg.get("message", "")
    customer_id = msg.get("customer_email") or msg.get("customer_phone") or "unknown"
    priority = msg.get("priority", "medium")

    agent = create_customer_success_agent()

    user_prompt = f"""
New customer message received!
Customer ID: {customer_id}
Customer Name: {customer_name}
Channel: {channel}
Priority: {priority}
Customer Email: {msg.get("customer_email", "unknown")}
Subject: {msg.get("subject", "No Subject")}
Thread ID: {msg.get("thread_id", "unknown")}

Message:
"{text}"

Please follow your Required Workflow. When you decide to reply to the customer, you MUST use the send_response tool.
For email and web_form channel responses, you MUST provide the following arguments to send_response:
- to_email: Use the 'Customer Email' provided above.
- subject: Use the 'Subject' provided above.
- thread_id: Use the 'Thread ID' provided above to ensure the reply stays in the same thread.
"""

    logger.info(f"Running agent for customer {customer_id} on channel {channel}")

    try:
        logger.info(f"Running Runner.run for customer {customer_id}")
        result = await Runner.run(agent, user_prompt, run_config=config)
        logger.info(f"Runner completed with final output length: {len(result.final_output) if result.final_output else 0}")
        return {
            "status": "success",
            "agent_output": result.final_output,
            "channel": channel,
            "customer_id": customer_id
        }
    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


def handle_customer_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper safe for worker/background threads."""
    loop = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(handle_customer_message_async(msg))
    except RuntimeError:
        return {
            "status": "error",
            "error": "handle_customer_message called inside an active event loop; use handle_customer_message_async"
        }
    finally:
        if loop is not None:
            try:
                loop.close()
            finally:
                asyncio.set_event_loop(None)


async def run_agent_sync_threadsafe(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibility async wrapper for call sites expecting async name."""
    return await handle_customer_message_async(msg)

if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)

    # Simple test run (Note: this requires valid tool implementations and DB connection
    # or it will fail on the tool calls, but it demonstrates the invocation structure).
    test_msg = {
        "channel": "email",
        "customer_email": "test@example.com",
        "message": "How do I invite teammates to my workspace?"
    }

    print("--- Running Test Message ---")
    response = handle_customer_message(test_msg)
    print(response)
