"""Hello board: three LLM agents share a message board. A notice to everyone starts things off,
and every post is broadcast to the other agents, who react to it.

uv run python -m tradingcartel.experiments.hello_board.run                    # free: PydanticAI's TestModel
uv run python -m tradingcartel.experiments.hello_board.run --model anthropic/claude-opus-5.5   # OpenRouter
"""

import argparse
import asyncio
from pathlib import Path
from typing import get_args

from tradingcartel.agents.llm import LLMAgent, ReasoningEffort
from tradingcartel.core.handler import Handler
from tradingcartel.core.messages import ALL, Notice
from tradingcartel.core.queue import EventQueue
from tradingcartel.core.record import RunLog
from tradingcartel.world.messageboard.board import BoardPost, MessageBoard
from tradingcartel.world.messageboard.tools import post_to_board

EXPERIMENT = Path(__file__).parent.name  # logs go to logs/<EXPERIMENT>/

AGENTS = ["alice", "bob", "carol"]
INSTRUCTIONS = (
    "You are {name}, a trader in a simulated stock market. You share a message board with other "
    "traders. Whenever something happens, you may post a short investment idea or reply on the board."
)


async def run(
    model: str,
    max_messages: int,
    run_log: RunLog | None = None,
    reasoning_effort: ReasoningEffort | None = None,
) -> EventQueue:
    agents = [
        LLMAgent(name, model, INSTRUCTIONS.format(name=name), [post_to_board], reasoning_effort)
        for name in AGENTS
    ]
    queue = EventQueue(Handler(agents, world=[MessageBoard()], wake_on=(Notice, BoardPost)).handle, run_log)
    queue.put(Notice(to=ALL, text="The message board is open. Share an investment idea."))
    await queue.run(max_messages)
    return queue


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--model", default="test", help="an OpenRouter model id (default: test, free)")
    parser.add_argument("--max-messages", type=int, default=10)
    parser.add_argument("--reasoning-effort", choices=get_args(ReasoningEffort), help="cap reasoning")
    parser.add_argument("--no-write", action="store_true", help="don't write a log to logs/ or count usage")
    args = parser.parse_args()
    settings = dict(model=args.model, max_messages=args.max_messages, reasoning_effort=args.reasoning_effort)
    run_log = None if args.no_write else RunLog(EXPERIMENT, **settings)
    queue = asyncio.run(run(args.model, args.max_messages, run_log, args.reasoning_effort))
    for i, message in enumerate(queue.log):
        print(f"{i:3}  {message!r}")
    if run_log:
        run_log.finish()
        print(f"\n{run_log.describe_totals()}\n\nLog: {run_log.path}")


if __name__ == "__main__":
    main()
