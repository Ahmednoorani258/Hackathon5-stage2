#!/usr/bin/env python3
"""
OpenAI Agents SDK Helper Script

This script provides common operations for working with the OpenAI Agents Python SDK.
"""

import argparse
import asyncio
from typing import Annotated
from pydantic import BaseModel, Field
from agents import Agent, Runner, SQLiteSession, function_tool


@function_tool
def calculator(operation: Annotated[str, "The mathematical operation to perform"],
               a: Annotated[float, "First operand"],
               b: Annotated[float, "Second operand"]) -> float:
    """Perform basic mathematical operations."""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    else:
        raise ValueError(f"Unknown operation: {operation}")


def create_simple_agent(name: str, instructions: str):
    """Create a simple agent with basic instructions."""
    return Agent(
        name=name,
        instructions=instructions,
        tools=[calculator]
    )


def run_simple_interaction(agent_name: str, instructions: str, user_input: str):
    """Run a simple agent interaction."""
    agent = create_simple_agent(agent_name, instructions)
    result = Runner.run_sync(agent, user_input)
    return result.final_output


def run_session_interaction(agent_name: str, instructions: str, messages: list, session_id: str = "default"):
    """Run an agent interaction with session memory."""
    agent = create_simple_agent(agent_name, instructions)
    session = SQLiteSession(session_id)

    for i, message in enumerate(messages):
        if i == len(messages) - 1:  # Last message gets the response
            result = Runner.run_sync(agent, message, session=session)
            return result.final_output
        else:  # Intermediate messages to build context
            Runner.run_sync(agent, message, session=session)

    return "No messages to process"


async def run_async_interaction(agent_name: str, instructions: str, user_input: str):
    """Run an asynchronous agent interaction."""
    agent = create_simple_agent(agent_name, instructions)
    result = await Runner.run(agent, user_input)
    return result.final_output


def main():
    parser = argparse.ArgumentParser(description="OpenAI Agents SDK Helper")
    parser.add_argument("--action", choices=["simple", "session", "async"], required=True,
                        help="Type of interaction to perform")
    parser.add_argument("--name", default="Assistant", help="Name of the agent")
    parser.add_argument("--instructions", default="You are a helpful assistant.",
                        help="Instructions for the agent")
    parser.add_argument("--input", help="Single input for simple interaction")
    parser.add_argument("--messages", nargs="+", help="Multiple messages for session interaction")
    parser.add_argument("--session-id", default="default", help="Session ID for session interaction")

    args = parser.parse_args()

    if args.action == "simple":
        if not args.input:
            print("Error: --input is required for simple action")
            return

        result = run_simple_interaction(args.name, args.instructions, args.input)
        print(f"Response: {result}")

    elif args.action == "session":
        if not args.messages:
            print("Error: --messages is required for session action")
            return

        result = run_session_interaction(args.name, args.instructions, args.messages, args.session_id)
        print(f"Response: {result}")

    elif args.action == "async":
        if not args.input:
            print("Error: --input is required for async action")
            return

        async def run_async():
            result = await run_async_interaction(args.name, args.instructions, args.input)
            print(f"Response: {result}")

        asyncio.run(run_async())


if __name__ == "__main__":
    main()