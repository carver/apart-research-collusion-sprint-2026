# tradingcartel

LLM agents trading on a simulated stock market, for studying when collusion emerges and what stops it (Apart Research AI Collusion Research Sprint, Track 1.1). Goals: `~/workspace/ai_safety_old/specs/IMPLEMENTATION_SPEC.md`.

## How it works

Everything is a message on **one running event queue**, and **one handler** processes every message.

```
EventQueue ──► Handler.handle(message) ──► world components update their state
                                       └─► agents the message is addressed to take a turn
               new messages from both ◄──┘  are queued at the current time
```

- **Simulated time:** every message has a `time`, in simulated minutes since the start. The queue always processes the earliest message next (ties in the order they were queued), and its clock jumps to each message's time. It never reads the computer's clock. Experiments schedule future events with `queue.put(message, delay=minutes)`.
- A message's `to` is one agent's name, `ALL` (a broadcast to every agent except the sender), or `None` (no agent receives it).
- **World components** (`tradingcartel/world/`) are plain objects with `handle(message) -> list[Message]`, such as the message board and, later, the order book. They hold state and never touch the queue.
- **Agents** run on PydanticAI and remember their whole conversation. Their tools don't change anything directly; they put messages in an outbox, which the handler returns to the queue.
- The run stops when no messages are left before the end time, or after `max_messages` (a cost brake).

## Layout

```
tradingcartel/
  core/          messages, the event queue, the handler (no market code)
  agents/        the PydanticAI agent (no market code)
  world/         one folder per world component: messageboard/ (later orderbook/, ...)
  experiments/   one folder per experiment
tests/
```

## Setup and run

Real models all go through OpenRouter. Put `OPENROUTER_API_KEY=...` in `.env` in the project root.

```bash
uv sync
uv run pytest                                                   # no API calls
uv run python -m tradingcartel.experiments.hello_board.run      # free: PydanticAI's TestModel
uv run python -m tradingcartel.experiments.hello_board.run --model anthropic/claude-opus-5.5 --max-messages 4
```

`--model` takes any OpenRouter model id (`anthropic/...`, `openai/...`, `google/...`).

## Dependencies

Only package versions released at least three weeks ago are used. `[tool.uv] exclude-newer` in `pyproject.toml` enforces this for every package, including transitive ones. Direct dependencies and the build backend are pinned with `==`, and `uv.lock` pins the rest.
