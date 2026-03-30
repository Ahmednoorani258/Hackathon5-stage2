---
name: openai-agents-sdk
description: |
  This skill provides guidance for implementing OpenAI Agents Python SDK features, including agents, tools, sessions, and handoffs.
  Use when users ask to implement agentic AI applications using OpenAI's Agents Python SDK for building production-ready agents.
---

# OpenAI Agents Python SDK Implementation Guide

## Overview

The OpenAI Agents Python SDK is a production-ready Python package for building agentic AI applications with minimal abstractions. It provides a clean, Python-first approach to creating AI agents that can use tools, maintain conversations, and handle complex workflows.

## Core Features

### Agents
- LLMs with instructions and tools
- Minimal abstractions for easy learning and use
- Built-in agent loop for tool calling

### Tools
- Function tools from Python functions with automatic schema generation
- Native Python approach using decorators and type hints
- Support for async and sync functions

### Sessions
- Automatic conversation history management
- SQLite-backed persistence for conversation state
- Context preservation across multiple interactions

### Handoffs
- Agent delegation for specific tasks
- Seamless handoff between specialized agents
- Flexible integration patterns

### Guardrails
- Input/output validation
- Built-in safety mechanisms
- Customizable validation rules

## Installation

```bash
pip install openai-agents
```

## Core Concepts

### Agent Creation
- Define agents with name, instructions, and tools
- Use minimal configuration for quick setup
- Leverage Python type hints for automatic schema generation

### Tool Integration
- Decorate Python functions with `@function_tool` for automatic tool creation
- Support for both sync and async functions
- Automatic JSON schema generation from type hints

### Session Management
- Use `SQLiteSession` for persistent conversation history
- Automatic context preservation across turns
- Support for advanced memory management

## Implementation Patterns

### Simple Agent Example
```python
from agents import Agent, Runner

# Create a basic agent
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant"
)

# Run a simple interaction
result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)
```

### Function Tools with Type Hints
```python
from typing import Annotated
from pydantic import BaseModel, Field
from agents import Agent, Runner, function_tool

# Define structured output type
class Weather(BaseModel):
    city: str = Field(description="The city name")
    temperature_range: str = Field(description="Temperature in Celsius")
    conditions: str = Field(description="Weather conditions")

# Create a function tool with decorator
@function_tool
def get_weather(city: Annotated[str, "The city to get weather for"]) -> Weather:
    """Get current weather information for a specified city."""
    # In production, this would call a real weather API
    return Weather(
        city=city,
        temperature_range="14-20C",
        conditions="Sunny with wind."
    )

# Create agent with tools
agent = Agent(
    name="Weather Assistant",
    instructions="You are a helpful weather assistant.",
    tools=[get_weather]
)

# Run with tool usage
result = Runner.run_sync(agent, "What's the weather in Tokyo?")
print(result.final_output)
```

### Session Management for Persistent Conversations
```python
from agents import Agent, Runner, SQLiteSession

# Create agent
agent = Agent(
    name="Assistant",
    instructions="Reply very concisely.",
)

# Create a session instance with a session ID
session = SQLiteSession("conversation_123")

# First turn
result = Runner.run_sync(
    agent,
    "What city is the Golden Gate Bridge in?",
    session=session
)
print(result.final_output)  # "San Francisco"

# Second turn - agent automatically remembers previous context
result = Runner.run_sync(
    agent,
    "What state is it in?",
    session=session
)
print(result.final_output)  # "California"
```

### Agent Handoffs for Specialized Tasks
```python
from agents import Agent

booking_agent = Agent(...)
refund_agent = Agent(...)

triage_agent = Agent(
    name="Triage agent",
    instructions=(
        "Help the user with their questions. "
        "If they ask about booking, hand off to the booking agent. "
        "If they ask about refunds, hand off to the refund agent."
    ),
    handoffs=[booking_agent, refund_agent],
)
```

### Advanced Tool with Context Wrapper
```python
from typing import Any
from typing_extensions import TypedDict
from agents import Agent, RunContextWrapper, function_tool

class Location(TypedDict):
    lat: float
    long: float

@function_tool
async def fetch_weather(location: Location) -> str:
    """Fetch the weather for a given location."""
    # In real life, we'd fetch the weather from a weather API
    return "sunny"

@function_tool(name_override="fetch_data")
def read_file(ctx: RunContextWrapper[Any], path: str, directory: str | None = None) -> str:
    """Read the contents of a file."""
    # In real life, we'd read the file from the file system
    return "<file contents>"

agent = Agent(
    name="Assistant",
    tools=[fetch_weather, read_file],
)
```

## Best Practices

1. **Python-First Approach**: Leverage Python type hints and native language features for cleaner code
2. **Tool Design**: Use Pydantic models for structured input/output schemas
3. **Session Management**: Implement persistent sessions for multi-turn conversations
4. **Agent Specialization**: Create specialized agents for specific tasks and use handoffs
5. **Error Handling**: Implement proper error handling for tool failures
6. **Async/Sync Consistency**: Choose between async and sync patterns consistently

## Security Considerations

- Validate all inputs to tools before processing
- Implement proper access controls for sensitive operations
- Sanitize outputs before displaying to users
- Use secure session storage mechanisms
- Implement rate limiting for tool usage

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing Python application structure, async patterns, and dependency management |
| **Conversation** | User's specific agent requirements, tool needs, and conversation patterns |
| **Skill References** | API patterns from `references/` (agents/tools/sessions management) |
| **User Guidelines** | Project-specific conventions, security requirements, and deployment patterns |

Ensure all required context is gathered before implementing.