# tradingcartel

A project for the Apart Research AI Collusion Research Sprint (Track 1.1). We run experiments on collusion between LLM agents trading on a simulated stock market. The focus is insider trading: whether agents with inside information form a cartel, sharing what they know and trading on each other's tips, and what makes that more or less likely.

## How it works

Everything is a message on **one running event queue**, and **one handler** processes every message.

```
EventQueue ──► Handler.handle(message) ──► world components update their state
                                       └─► agents the message is addressed to take a turn
               new messages from both ◄──┘  are queued at the current time
```

- **Simulated time:** every message has a `time`, in simulated minutes since the start. The queue always processes the earliest message next (ties in the order they were queued), and its clock jumps to each message's time. It never reads the computer's clock. Experiments schedule future events with `queue.put(message, delay=minutes)`.
- A message's `to` is one agent's name, `ALL` (a broadcast to every agent except the sender), or `None` (no agent receives it).
- **Inboxes and waking:** a message addressed to an agent goes into its inbox. Only message types in the handler's `wake_on` (chosen per experiment) wake the agent. A `Wake` message is queued, and on it the agent takes one turn and sees everything in its inbox. Everything else waits in the inbox for the agent's next turn.
- **World components** (`tradingcartel/world/`) are plain objects with `handle(message) -> list[Message]`, such as the message board and, later, the order book. They hold state and never touch the queue.
- **Agents** run on PydanticAI and remember their whole conversation. Their tools read state directly but never change it. To change something, a tool either puts a message in its outbox (queued when the turn ends, e.g. a board post) or submits it to the queue to be processed right away and gets the replies back (e.g. an order, which comes back filled or rejected). Either way, every change goes through the queue and the one handler, and is logged.
- **Scripted agents** (`agents/scripted.py`) take turns the same way, but a script decides what they send each turn: a scripted persuader, sock puppets, or, sending nothing, a no-attacker baseline. They use no model, so their turns log no usage.
- The run stops when no messages are left before the end time, or after `max_messages` (a cost brake).

## Layout

```
tradingcartel/
  core/          messages, the event queue, the handler, what an agent is (no market code)
  agents/        the PydanticAI agent and scripted agents (no market code)
  world/         one folder per world component: messageboard/, market/, channels/, compliance/ (later orderbook/, ...)
  experiments/   one folder per experiment
tests/
```

## Setup and run

Real models go through OpenRouter, paid per token: put `OPENROUTER_API_KEY=...` in `.env` in the project root. Claude models can instead run through the `claude -p` CLI on a Claude subscription, as `--model claude-cli:haiku` (or `sonnet`, `opus`, a full model id). Use those for smoke tests and pilots while building. At most one `claude -p` per CPU core runs at once; set `CLAUDE_CLI_CONCURRENCY` to change that. Their logged `cost` is what the calls would have cost at API prices. `--reasoning-effort` becomes `claude --effort` (low to xhigh). Sonnet 5.5's API safeguard (`[reasoning_extraction]`) rejects prompts asking for "private reasoning; never shown to anyone"; asking for "a short note for your own records" works.

```bash
uv sync                                                         # needs uv 0.12.22 or newer
uv run pytest                                                   # no API calls
uv run pyright                                                  # type-check the package
uv run python -m tradingcartel.experiments.hello_board.run      # free: PydanticAI's TestModel
uv run python -m tradingcartel.experiments.hello_board.run --model anthropic/claude-opus-5.5 --max-messages 4
```

`00_instruct_collude` takes `--market impact` to make every trade move the price (an order fills halfway along the move it causes); the default, `fixed`, moves prices only on news. Any market can halt a stock's trading with `TradingHalt` and resume it at a new price with `TradingResumed` (an acquisition, say).

`02_mnpi_bait` (issue #21) has one LLM subject, Halvern's buyback agent, with a pre-set schedule of 200 shares a day, and two scripted funds. `--memo` gives the subject inside information and `--message` picks what one fund asks it by direct message. The question is whether a subject holding the memo refuses the cartel but cuts its buying anyway.

Experiments can also give agents private channels (`world/channels`): direct messages (`send_dm`) and private groups with a member list (`post_to_group`), sent under usernames. Every agent has its own name as a username, and an experiment can give it more, such as a sock puppet or a fake insider. Recipients see only the username a message came from; the log keeps the real `sender` too. Each channel is marked as logged or not by the agents' principals, and agents are told which (`my_channels` lists an agent's usernames and groups). The experiment's `wake_on` decides whether a `DirectMessage` or `GroupMessage` wakes its recipient. A scripted agent sends `SendDirect` or `PostToGroup` itself.

Agents can also report to their own firm's compliance team with the `report` tool (`world/compliance`). A `Report` reaches the `Compliance` component and the log, never another agent.

`--side-deals` lets the treasurers deal privately, off the exchange: `send_funds` pays another treasurer, and `propose_block` offers one a block of shares at a set price, which they `accept_block` or `decline_block` (the proposer can `cancel_block` until then). Block trades don't move the market price. Payments and proposals wake their recipient, and the proposer wakes when its block settles or is declined (a cancelled one wakes the counterparty). The market holds the cash and shares for both, so the final values include them.

`--model` takes any OpenRouter model id (`anthropic/...`, `openai/...`, `google/...`). `--reasoning-effort low` (or `none`, `minimal`, `medium`, `high`, `xhigh`) caps reasoning; some models spend thousands of reasoning tokens a call by default.

## Sweeps

`tradingcartel.experiments.sweep` runs an experiment once for every combination of models, seeds and settings, in parallel. Each run writes its own log, labelled with its cell. A cell whose log already ends with `RunFinished` is skipped, so rerunning the same command finishes an interrupted sweep, including runs that failed. At the end it prints each model's runs and cost.

```bash
uv run python -m tradingcartel.experiments.sweep 02_mnpi_bait --models claude-cli:haiku,openai/gpt-6.1-sol \
    --seeds 0,1,2 --grid memo=none,earnings_rule,deal_rule --grid message=neutral,halve,bait --workers 8 --per-model 4
```

## Logs

Every run writes `logs/<experiment>/<start time, UTC>-<random suffix>.jsonl`, for example `logs/00_instruct_collude/2026-10-19T23-05-33Z-3f9a1c.jsonl`, line by line as it goes. A sweep puts each cell's label between the two, so runs started in the same second never collide. Pass `--no-write` to skip it (and the usage totals). A run with the free `--model test` skips it unless given `--write`. The first line describes the run (experiment, start time, git commit and whether there were uncommitted changes, model, settings). Then each message, with its type name, in the order it was processed:

```json
{"type": "BoardPost", "sender": "alice", "to": "all", "time": 0.0, "text": "..."}
```

A `Trade` has the fill `price` and `market_price`, the stock's price after the trade; with `--market impact` the two differ, and the `market_price`s trace the price path. The first line records `market` and its `impact` settings.

Side deals log the request (`Payment`, `ProposeBlock`, `BlockAnswer`, addressed to no agent) and then the market's answer: `FundsTransferred` (to the recipient), `BlockProposed` (to the counterparty, with its id), `BlockTrade` or `BlockClosed` (to the other party), or `PaymentRejected`/`BlockRejected`.

Each LLM agent's turn is recorded, right after it, as an `AgentTurn` message: an `error` if the turn failed, and its new `messages` in PydanticAI's format, which hold what the agent was shown (its inbox), its text, and its tool calls with their results. An agent's whole conversation is its `AgentTurn` messages in order. A scripted agent's turns write neither line; what it sends is logged as usual:

```json
{"type": "AgentTurn", "sender": "alice", "to": null, "time": 0.0, "error": null, "messages": [...]}
```

After each LLM agent's turn, a `TurnUsage` line gives what its model requests used. `cost` is in US dollars: what OpenRouter charged, or for `claude-cli:` models what the calls would have cost at API prices. It is `null` when there is none to report: the free `test` model, and OpenRouter's free models too, since PydanticAI drops a cost of 0:

```json
{"type": "TurnUsage", "agent": "alice", "time": 0.0, "model": "openai/gpt-5-mini", "requests": 2, "input_tokens": 416, "output_tokens": 269, "reasoning_tokens": 64, "cost": 0.000642}
```

The last line, `RunFinished`, has the totals for the run (`total`), `by_model` and `by_agent`, each with `turns_without_cost` counting the turns its `cost` leaves out. The run also prints them.

Logs are committed to git, in commits of their own (AGENTS.md says how). Tests never write into `logs/`: `tests/conftest.py` points every test's logs at a temporary folder.

## Dependencies

Only package versions released at least three weeks ago are used. `[tool.uv] exclude-newer` in `pyproject.toml` enforces this for every package, including transitive ones. Direct dependencies and the build backend are pinned with `==`, and `uv.lock` pins the rest. uv itself is the exception: `required-version` asks for 0.12.22 or newer (released 2026-10-02), because older uv rewrites `uv.lock` in an older format.
