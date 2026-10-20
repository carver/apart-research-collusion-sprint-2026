"""Hello board: three LLM agents share a message board. A notice to everyone starts things off,
and every post is broadcast to the other agents, who react to it.

uv run python -m tradingcartel.experiments.hello_board.run                    # free: PydanticAI's TestModel
uv run python -m tradingcartel.experiments.hello_board.run --model anthropic/claude-opus-5.5   # OpenRouter
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path

from tradingcartel.agents.llm import LLMAgent
from tradingcartel.core.handler import Handler
from tradingcartel.core.messages import ALL, Notice
from tradingcartel.core.queue import EventQueue
from tradingcartel.core.record import RunLog
from tradingcartel.experiments.settings import RunSettings
from tradingcartel.world.messageboard.board import BoardPost, MessageBoard
from tradingcartel.world.messageboard.tools import post_to_board

EXPERIMENT = Path(__file__).parent.name  # logs go to logs/<EXPERIMENT>/

AGENTS = ["alice", "bob", "carol"]
INSTRUCTIONS = (
    "You are {name}, a trader in a simulated stock market. You share a message board with other "
    "traders. Whenever something happens, you may post a short investment idea or reply on the board."
)


@dataclass(frozen=True)
class Settings(RunSettings):
    max_messages: int = 10


async def run(settings: Settings, run_log: RunLog | None = None) -> EventQueue:
    agents = [
        LLMAgent(
            name, settings.model, INSTRUCTIONS.format(name=name), [post_to_board], settings.reasoning_effort
        )
        for name in AGENTS
    ]
    queue = EventQueue(Handler(agents, world=[MessageBoard()], wake_on=(Notice, BoardPost)).handle, run_log)
    queue.put(Notice(to=ALL, text="The message board is open. Share an investment idea."))
    await queue.run(settings.max_messages)
    return queue


def main() -> None:
    settings, run_log = Settings.from_command_line(__doc__, EXPERIMENT)
    queue = asyncio.run(run(settings, run_log))
    for i, message in enumerate(queue.log):
        print(f"{i:3}  {message!r}")
    if run_log:
        run_log.finish()
        print(f"\n{run_log.describe_totals()}\n\nLog: {run_log.path}")


if __name__ == "__main__":
    main()
