import logging
from typing import Dict, Any

from agents import Agent, Runner
from production.agent.setup_config import config

from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from production.agent.tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
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
            get_customer_history,
            search_knowledge_base,
            send_response,
            escalate_to_human
        ]
    )

def handle_customer_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an incoming customer message using the OpenAI Agents SDK.

    Args:
        msg: Incoming message payload with fields like:
             channel, customer_name, customer_email, customer_phone, message, priority
    """
    # Normalize inputs
    channel = msg.get("channel", "unknown")
    customer_name = msg.get("customer_name") or msg.get("customer_email") or msg.get("customer_phone") or "Customer"
    text = msg.get("message", "")
    customer_id = msg.get("customer_email") or msg.get("customer_phone") or "unknown"
    priority = msg.get("priority", "medium")

    # Create the agent
    agent = create_customer_success_agent()

    # Format the prompt for the agent to kick off its workflow
    user_prompt = f"""
New customer message received!
Customer ID: {customer_id}
Customer Name: {customer_name}
Channel: {channel}
Priority: {priority}

Message:
"{text}"

Please follow your Required Workflow.
"""

    logger.info(f"Running agent for customer {customer_id} on channel {channel}")

    # Run the agent synchronously (using run_sync per OpenAI Agents SDK docs)
    # The agent will autonomouslly call tools like create_ticket, search_kb, and send_response.
    try:
        # Note: If memory/sessions are needed across turns, we would use Runner.run_sync()
        # with a session state instead of treating it as a new run each time.
        # But for this event-driven handler where state is pulled from DB via tools,
        # a fresh run with context variables is fine.
        result = Runner.run_sync(agent, user_prompt ,run_config=config)

        # The agent should have used the send_response tool to reply,
        # but we also return its final internal summary/output
        return {
            "status": "success",
            "agent_output": result.final_output,
            "channel": channel,
            "customer_id": customer_id
        }
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

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
