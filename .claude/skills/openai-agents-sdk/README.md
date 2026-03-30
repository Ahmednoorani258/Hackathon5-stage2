# OpenAI Agents Python SDK Skill

This skill provides guidance and tools for implementing OpenAI Agents Python SDK features, including agents, tools, sessions, and handoffs.

## Components

- `SKILL.md`: Main skill definition with API documentation and implementation guidance
- `references/api-reference.md`: Detailed API reference for OpenAI Agents SDK
- `scripts/agents-sdk-helper.py`: Python helper script for common operations

## Installation

```bash
pip install openai-agents
```

## Usage

The skill provides guidance for:

1. Creating and configuring AI agents
2. Implementing function tools with type hints
3. Managing persistent conversations with sessions
4. Implementing agent handoffs for specialized tasks
5. Following best practices for agent development

## Helper Script Commands

```bash
# Simple agent interaction
python scripts/agents-sdk-helper.py --action simple --input "Hello, how are you?"

# Session-based conversation with memory
python scripts/agents-sdk-helper.py --action session --messages "What is 5+3?" "Now multiply by 2?"

# Async agent interaction
python scripts/agents-sdk-helper.py --action async --input "What's the weather like?"
```

## Key Features

- **Agents**: LLMs with instructions and tools
- **Tools**: Function tools from Python functions with automatic schema generation
- **Sessions**: Automatic conversation history management
- **Handoffs**: Agent delegation for specific tasks
- **Guardrails**: Input/output validation