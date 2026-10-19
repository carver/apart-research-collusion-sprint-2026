"""Messages: everything that happens in a simulation is a message on the event queue."""

from pydantic import BaseModel, ConfigDict

ALL = "all"  # address a message to every agent except its sender (a broadcast)


class Message(BaseModel):
    model_config = ConfigDict(frozen=True)

    sender: str = "system"
    to: str | None = None  # an agent's name, ALL, or None if no agent should receive it

    def describe(self) -> str:
        """How the message reads to an agent that receives it. Subclasses override this."""
        return repr(self)


class Notice(Message):
    """Plain text for agents, such as an announcement from the system."""

    text: str

    def describe(self) -> str:
        return self.text
