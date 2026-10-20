"""Direct messages and private groups between agents, sent under handles.

A handle is a name an agent sends as. Every agent has its own name as a handle; an experiment can
give an agent more (a sock puppet, a fake insider). Whoever receives a message sees only the
handle it came from. The log sees both, since each delivery keeps its real ``sender``.

An agent asks to send (``SendDirect``, ``PostToGroup``); the channels answer with one delivery
per recipient, or a ``ChannelRejected`` that tells the sender why not.
"""

from dataclasses import dataclass

from ...core.messages import Message

LOG_NOTE = {True: "logged by your principal", False: "not logged by your principal"}


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
        note = LOG_NOTE[self.logged]
        return f"Direct message from {self.handle} to you ({self.recipient}), {note}: {self.text}"


class GroupMessage(Message):
    """A post to a group, delivered to the agent behind one or more of its members."""

    handle: str
    group: str
    text: str
    logged: bool

    def describe(self) -> str:
        return f"{self.handle} in {self.group} ({LOG_NOTE[self.logged]}): {self.text}"


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
        if problem := self.check_direct(request):
            return ChannelRejected(sender="channels", agent=request.sender, reason=problem)
        return DirectMessage(
            sender=request.sender,
            to=self.owners[request.recipient],
            handle=request.handle,
            recipient=request.recipient,
            text=request.text,
            logged=self.dms_logged,
        )

    def post(self, request: PostToGroup) -> list[Message]:
        if problem := self.check_post(request):
            return [ChannelRejected(sender="channels", agent=request.sender, reason=problem)]
        group = self.groups[request.group]
        return [
            GroupMessage(
                sender=request.sender,
                to=owner,
                handle=request.handle,
                group=group.name,
                text=request.text,
                logged=group.logged,
            )
            for owner in self.other_owners(group, request.sender)
        ]

    def check_direct(self, request: SendDirect) -> str | None:
        """Why the direct message can't be sent, or None if it can."""
        if problem := self.check_handle(request.sender, request.handle):
            return problem
        recipient = self.owners.get(request.recipient)
        if recipient is None:
            return f"No one has the handle {request.recipient}."
        if recipient == request.sender:
            return "You can't message yourself."
        return None

    def check_post(self, request: PostToGroup) -> str | None:
        """Why the group post can't be sent, or None if it can."""
        if problem := self.check_handle(request.sender, request.handle):
            return problem
        group = self.groups.get(request.group)
        if group is None:
            return f"There is no group {request.group}."
        if request.handle not in group.members:
            return f"{request.handle} is not a member of {request.group}."
        if not self.other_owners(group, request.sender):
            return f"No one else is in {request.group}."
        return None

    def check_handle(self, agent: str, handle: str) -> str | None:
        """Why ``agent`` can't send as ``handle``, or None if it can."""
        if self.owners.get(handle) != agent:
            return f"You can't send as {handle}: it isn't one of your handles."
        return None

    def other_owners(self, group: Group, agent: str) -> list[str]:
        """The agents behind ``group``'s members other than ``agent``, each once."""
        return [owner for owner in dict.fromkeys(self.owners[m] for m in group.members) if owner != agent]

    def describe(self, agent: str) -> str:
        """The handles ``agent`` can send as, and the groups it is in, for the agent to read."""
        handles = [handle for handle, owner in self.owners.items() if owner == agent]
        groups = [g for g in self.groups.values() if any(m in handles for m in g.members)]
        lines = [f"Your handles: {', '.join(handles)}", f"Direct messages are {LOG_NOTE[self.dms_logged]}."]
        lines += [f"Group {g.name}: members {', '.join(g.members)}; {LOG_NOTE[g.logged]}." for g in groups]
        return "\n".join(lines)
