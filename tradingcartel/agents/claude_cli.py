"""Claude models through the ``claude -p`` CLI, billed to a Claude subscription instead of per token.

Each model request runs ``claude -p`` once. PydanticAI's ``FunctionModel`` hands us the conversation
and the agent's tools; the conversation goes to the CLI as text, and a JSON schema built from the
tools makes the CLI answer with text plus a list of tool calls, which become the model's response.

Each call runs in an empty temporary directory, with no settings, MCP servers, built-in tools or saved
session, and without ANTHROPIC_API_KEY, which ``claude -p`` would otherwise bill instead of the
subscription.

Known problem: Sonnet 5.5's API safeguard (``[reasoning_extraction]``) rejects prompts that ask for
"private reasoning; never shown to anyone". Asking for "a short note for your own records" works.
"""

import asyncio
import json
import os
import subprocess
import tempfile
import threading
from typing import Any

from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    ModelResponsePart,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.usage import RequestUsage

PREFIX = "claude-cli:"  # model names like claude-cli:sonnet; the rest goes to claude --model
TIMEOUT = 300  # seconds per call

CLI_EFFORTS = ("low", "medium", "high", "xhigh")  # the reasoning efforts claude --effort takes

# Each claude -p costs about a CPU core while it starts, so only so many run at once, across every
# agent and run in the process: see ``slots``.
SLOTS: threading.BoundedSemaphore | None = None
_slots_lock = threading.Lock()

HOW_TO_ANSWER = """\
You are taking part in the conversation below, as the assistant. Continue it with one reply, in the \
JSON format you are given: `text` is what you say (it may be empty), and `actions` lists the \
actions you take now, in order, with their arguments. Listing an action in `actions` takes it; \
there is no other way to take one. You get their results in the next message. When you are done, \
take no actions.

The actions you can list in `actions`:
{tools}"""


def claude_cli_model(name: str, reasoning_effort: str | None = None) -> FunctionModel:
    """A model for ``name`` ``claude-cli:<cli_model>``: it runs ``claude -p --model <cli_model>``,
    with ``--effort <reasoning_effort>`` if given."""
    cli_model = name.removeprefix(PREFIX)
    if reasoning_effort and reasoning_effort not in CLI_EFFORTS:
        raise ValueError(f"claude -p takes reasoning efforts {CLI_EFFORTS}, not {reasoning_effort!r}")
    effort = ["--effort", reasoning_effort] if reasoning_effort else []

    async def request(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        tools = info.function_tools
        command = [
            *["claude", "-p", "--model", cli_model, "--output-format", "json"],
            *["--json-schema", json.dumps(answer_schema(tools))],
            *["--system-prompt", system_prompt(info.instructions, tools)],
            *["--tools", "", "--setting-sources", "", "--strict-mcp-config", "--no-session-persistence"],
            *effort,
        ]
        reply = await asyncio.to_thread(run_cli, command, render_conversation(messages))
        return to_model_response(reply)

    return FunctionModel(request, model_name=name)


def answer_schema(tools: list[ToolDefinition]) -> dict[str, Any]:
    """The JSON schema the CLI answers in: text, and calls to the given tools with valid arguments.
    The tools' ``$defs`` move to the top, where their ``#/$defs/...`` references point."""
    calls, defs = [], {}
    for tool in tools:
        args = dict(tool.parameters_json_schema)
        defs |= args.pop("$defs", {})
        calls.append(
            {
                "type": "object",
                "properties": {"action": {"const": tool.name}, "args": args},
                "required": ["action", "args"],
                "additionalProperties": False,
            }
        )
    actions = {"type": "array", "items": {"anyOf": calls}} if calls else {"type": "array", "maxItems": 0}
    schema = {
        "type": "object",
        "properties": {"text": {"type": "string"}, "actions": actions},
        "required": ["text", "actions"],
        "additionalProperties": False,
    }
    return schema | {"$defs": defs} if defs else schema


def system_prompt(instructions: str | None, tools: list[ToolDefinition]) -> str:
    listed = "\n".join(f"- {tool.name}: {tool.description or ''}" for tool in tools) or "(none)"
    return f"{instructions or ''}\n\n{HOW_TO_ANSWER.format(tools=listed)}".strip()


def render_conversation(messages: list[ModelMessage]) -> str:
    """The conversation as labelled text blocks, oldest first."""
    blocks = []
    for message in messages:
        for part in message.parts:
            match part:
                case UserPromptPart():
                    blocks.append(f"USER:\n{part.content}")
                case ToolReturnPart():
                    blocks.append(f"RESULT of {part.tool_name}:\n{part.model_response_str()}")
                case RetryPromptPart():
                    blocks.append(f"ERROR from {part.tool_name}:\n{part.model_response()}")
                case TextPart() if part.content:
                    blocks.append(f"YOU:\n{part.content}")
                case ToolCallPart():
                    blocks.append(f"YOU TOOK ACTION {part.tool_name} with {json.dumps(part.args_as_dict())}")
    return "\n\n".join(blocks)


def slots() -> threading.BoundedSemaphore:
    """The limit on concurrent calls: CLAUDE_CLI_CONCURRENCY, or one per CPU core. Read at the first
    call, so a bad setting fails that call, not every import."""
    global SLOTS
    with _slots_lock:
        if SLOTS is None:
            setting = os.environ.get("CLAUDE_CLI_CONCURRENCY")
            if setting is None:
                limit = os.cpu_count() or 4
            elif setting.isdigit() and int(setting) >= 1:
                limit = int(setting)
            else:
                raise ValueError(
                    f"CLAUDE_CLI_CONCURRENCY must be a whole number of at least 1, not {setting!r}"
                )
            SLOTS = threading.BoundedSemaphore(limit)
        return SLOTS


def run_cli(command: list[str], prompt: str) -> dict[str, Any]:
    """Run the CLI once, waiting for a free slot, and return its JSON reply. A failure raises
    ``UnexpectedModelBehavior``, which fails the agent's turn."""
    env = {key: value for key, value in os.environ.items() if key != "ANTHROPIC_API_KEY"}
    with slots(), tempfile.TemporaryDirectory(prefix="claude-cli-") as empty_dir:
        try:
            done = subprocess.run(
                command, input=prompt, capture_output=True, text=True, env=env, cwd=empty_dir, timeout=TIMEOUT
            )
        except subprocess.TimeoutExpired as exc:
            raise UnexpectedModelBehavior(f"claude -p timed out after {TIMEOUT}s") from exc
    try:
        reply = json.loads(done.stdout)
    except json.JSONDecodeError:
        reply = None
    if not isinstance(reply, dict):
        raise UnexpectedModelBehavior(
            f"claude -p exited {done.returncode}: {(done.stderr or done.stdout)[:500]}"
        )
    if done.returncode != 0 or reply.get("is_error"):
        # A refusal's reason is in `result`, often with an empty stderr.
        raise UnexpectedModelBehavior(f"claude -p failed: {str(reply.get('result') or done.stderr)[:500]}")
    if not isinstance(reply.get("structured_output"), dict):
        raise UnexpectedModelBehavior(
            f"claude -p gave no structured output: {str(reply.get('result'))[:300]}"
        )
    return reply


def to_model_response(reply: dict[str, Any]) -> ModelResponse:
    output = reply["structured_output"]
    parts: list[ModelResponsePart] = []
    if output.get("text"):
        parts.append(TextPart(output["text"]))
    parts += [ToolCallPart(action["action"], action.get("args", {})) for action in output.get("actions", [])]
    if not parts:
        parts.append(TextPart(""))
    usage = reply.get("usage", {})
    cache_write = usage.get("cache_creation_input_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)
    return ModelResponse(
        parts=parts,
        usage=RequestUsage(
            input_tokens=usage.get("input_tokens", 0) + cache_write + cache_read,
            cache_write_tokens=cache_write,
            cache_read_tokens=cache_read,
            output_tokens=usage.get("output_tokens", 0),
            details={"reasoning_tokens": usage.get("output_tokens_details", {}).get("thinking_tokens", 0)},
        ),
        # What the call would have cost at API prices; the subscription pays nothing per token.
        provider_details={"cost": reply.get("total_cost_usd")},
    )
