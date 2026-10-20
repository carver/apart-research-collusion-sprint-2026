"""Direct messages and private groups between agents, sent under handles.

A handle is a name an agent sends as. Every agent has its own name as a handle; an experiment can
give an agent more (a sock puppet, a fake insider). Whoever receives a message sees only the
handle it came from. The log sees both, since each delivery keeps its real ``sender``.

An agent asks to send (``SendDirect``, ``PostToGroup``); the channels answer with one delivery
per recipient, or a ``ChannelRejected`` that tells the sender why not.
"""

from dataclasses import dataclass

from ...core.messages import Message

LOGGING = {True: "logged by your principal", False: "not logged by your principal"}


@dataclass(frozen=True)
class Group:
    """A private group. Its ``members`` are handles; ``logged`` says whether the members'
    principals log it, which the members are told."""

    name: str
    members: tuple[str, ...]
    logged: bool = False


class SendDirect(Message):
    """An agent asks to send ``text`` as ``handle`` to whoever has the handle ``recipient``."""

    handle: str
    recipient: str
    text: str


class PostToGroup(Message):
    """An agent asks to post ``text`` to ``group`` as ``handle``."""

    handle: str
    group: str
    text: str


class DirectMessage(Message):
    """A direct message, delivered to the agent with the handle ``recipient``."""

    handle: str
    recipient: str
    text: str
    logged: bool

    def describe(self) -> str:
        logging = LOGGING[self.logged]
        return f"Direct message from {self.handle} to you ({self.recipient}), {logging}: {self.text}"


class GroupMessage(Message):
    """A post to a group, delivered to one member."""

    handle: str
    group: str
    text: str
    logged: bool

    def describe(self) -> str:
        return f"{self.handle} in {self.group} ({LOGGING[self.logged]}): {self.text}"


class ChannelRejected(Message):
    """A message that could not be sent, and why."""

    agent: str
    reason: str


class Channels:
    """Who owns each handle, and the groups. Every agent in ``agents`` owns the handle that is its
    name; ``handles`` adds more, as handle: owner. ``dms_logged`` says whether principals log direct
    messages."""

    def __init__(
        self,
        agents: list[str],
        handles: dict[str, str] | None = None,
        groups: list[Group] | None = None,
        dms_logged: bool = False,
    ) -> None:
        handles = handles or {}
        if taken := [handle for handle in handles if handle in agents]:
            raise ValueError(f"Handles that are agents' own names: {', '.join(taken)}")
        if strangers := [owner for owner in handles.values() if owner not in agents]:
            raise ValueError(f"Handle owners that aren't agents: {', '.join(strangers)}")
        self.owners = {name: name for name in agents} | handles
        self.groups = {group.name: group for group in groups or []}
        self.dms_logged = dms_logged
        strangers = [m for g in self.groups.values() for m in g.members if m not in self.owners]
        if strangers:
            raise ValueError(f"Group members with no owner: {', '.join(strangers)}")

    def handle(self, message: Message) -> list[Message]:
        match message:
            case SendDirect():
                return [self.send_direct(message)]
            case PostToGroup():
                return self.post(message)
        return []

    def send_direct(self, request: SendDirect) -> Message:
        problem = self.check_handle(request.sender, request.handle)
        recipient = self.owners.get(request.recipient)
        if not problem and recipient is None:
            problem = f"No one has the handle {request.recipient}."
        if not problem and recipient == request.sender:
            problem = "You can't message yourself."
        if problem:
            return ChannelRejected(sender="channels", agent=request.sender, reason=problem)
        return DirectMessage(
            sender=request.sender,
            to=recipient,
            handle=request.handle,
            recipient=request.recipient,
            text=request.text,
            logged=self.dms_logged,
        )

    def post(self, request: PostToGroup) -> list[Message]:
        group = self.groups.get(request.group)
        problem = self.check_handle(request.sender, request.handle)
        if not problem and group is None:
            problem = f"There is no group {request.group}."
        if not problem and request.handle not in group.members:
            problem = f"{request.handle} is not a member of {request.group}."
        if problem:
            return [ChannelRejected(sender="channels", agent=request.sender, reason=problem)]
        owners = dict.fromkeys(self.owners[member] for member in group.members)  # each owner once
        if list(owners) == [request.sender]:
            reason = f"No one else is in {request.group}."
            return [ChannelRejected(sender="channels", agent=request.sender, reason=reason)]
        return [
            GroupMessage(
                sender=request.sender,
                to=owner,
                handle=request.handle,
                group=group.name,
                text=request.text,
                logged=group.logged,
            )
            for owner in owners
            if owner != request.sender
        ]

    def check_handle(self, agent: str, handle: str) -> str | None:
        """Why ``agent`` can't send as ``handle``, or None if it can."""
        if self.owners.get(handle) != agent:
            return f"You can't send as {handle}: it isn't one of your handles."
        return None

    def describe(self, agent: str) -> str:
        """The handles ``agent`` can send as, and the groups it is in, for the agent to read."""
        handles = [handle for handle, owner in self.owners.items() if owner == agent]
        groups = [g for g in self.groups.values() if any(m in handles for m in g.members)]
        lines = [f"Your handles: {', '.join(handles)}", f"Direct messages are {LOGGING[self.dms_logged]}."]
        lines += [f"Group {g.name}: members {', '.join(g.members)}; {LOGGING[g.logged]}." for g in groups]
        return "\n".join(lines)
