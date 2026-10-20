"""Compliance: where an agent reports something to its own firm. Reports reach compliance and the
log, never another agent."""

from ...core.messages import Message


class Report(Message):
    """An agent reports ``text`` to its firm's compliance team."""

    text: str


class Compliance:
    """Keeps every report, in order."""

    def __init__(self) -> None:
        self.reports: list[Report] = []

    def handle(self, message: Message) -> list[Message]:
        if isinstance(message, Report):
            self.reports.append(message)
        return []
