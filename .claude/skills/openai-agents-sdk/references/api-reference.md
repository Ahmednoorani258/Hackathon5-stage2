# OpenAI Agents Python SDK API Reference

## Core Classes

### Agent
The main class for creating AI agents with instructions and tools.

**Constructor Parameters:**
- `name` (str): Name of the agent
- `instructions` (str): System instructions for the agent
- `tools` (list, optional): List of tools available to the agent
- `handoffs` (list, optional): List of agents to hand off to for specific tasks

**Usage:**
```python
from agents import Agent

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant",
    tools=[weather_tool, search_tool]
)
```

### Runner
Class for executing agent runs with or without sessions.

**Static Methods:**
- `run_sync(agent, input, session=None)`: Synchronous execution of an agent run
- `run(agent, input, session=None)`: Asynchronous execution of an agent run

**Usage:**
```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Help the user.")
result = Runner.run_sync(agent, "Hello, how are you?")
print(result.final_output)
```

### SQLiteSession
Class for managing persistent conversation sessions using SQLite.

**Constructor Parameters:**
- `session_id` (str): Unique identifier for the session
- `db_path` (str, optional): Path to SQLite database file (default: in-memory)

**Usage:**
```python
from agents import SQLiteSession

session = SQLiteSession("conversation_123", "conversations.db")
```

## Decorators

### @function_tool
Decorator to convert Python functions into agent tools with automatic schema generation.

**Parameters:**
- `name_override` (str, optional): Override the function name for the tool

**Usage:**
```python
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: sunny"
```

## Advanced Classes

### RunContextWrapper
Wrapper class providing context during tool execution.

**Usage:**
```python
from agents import RunContextWrapper, function_tool

@function_tool
def read_file(ctx: RunContextWrapper[Any], path: str) -> str:
    """Read a file with context access."""
    # Access to execution context
    return "file contents"
```

### FunctionTool
Class for creating tools programmatically.

**Constructor Parameters:**
- `name` (str): Tool name
- `description` (str): Tool description
- `params_json_schema` (dict): JSON schema for parameters
- `on_invoke_tool` (callable): Function to execute when tool is called

## Result Objects

### RunResult
Object returned by agent runs containing the final output and metadata.

**Properties:**
- `final_output` (str): The final output from the agent run

## Session Extensions

### AdvancedSQLiteSession
Enhanced session with additional memory management capabilities.

**Constructor Parameters:**
- `session_id` (str): Unique identifier for the session
- `db_path` (str): Path to SQLite database file
- `create_tables` (bool): Whether to create database tables automatically

**Methods:**
- `store_run_usage(result)`: Store usage statistics for the run

## Design Patterns

### Agent Handoff Pattern
Use when you need specialized agents for different tasks:

```python
booking_agent = Agent(...)
refund_agent = Agent(...)

customer_facing_agent = Agent(
    name="Customer-facing agent",
    instructions="Handle all direct user communication.",
    tools=[
        booking_agent.as_tool(
            tool_name="booking_expert",
            tool_description="Handles booking questions and requests.",
        ),
        refund_agent.as_tool(
            tool_name="refund_expert",
            tool_description="Handles refund questions and requests.",
        )
    ],
)
```

### Tool Composition Pattern
Use when you want to combine multiple tools:

```python
from agents import Agent, Runner, function_tool

@function_tool
def search_web(query: str) -> str:
    """Search the web for information."""
    return "search results"

@function_tool
def summarize(text: str) -> str:
    """Summarize a text."""
    return "summary"

agent = Agent(
    name="Research Assistant",
    instructions="Help with research tasks.",
    tools=[search_web, summarize]
)
```

### Session Continuation Pattern
Use for maintaining context across multiple interactions:

```python
from agents import Agent, Runner, SQLiteSession

agent = Agent(name="Assistant", instructions="Remember previous conversation.")

# Use same session ID across multiple interactions
session = SQLiteSession("user_123_conversation")

# Each interaction preserves context from previous ones
result1 = Runner.run_sync(agent, "What is the capital of France?", session=session)
result2 = Runner.run_sync(agent, "What about the population?", session=session)  # Knows we're still talking about France
```