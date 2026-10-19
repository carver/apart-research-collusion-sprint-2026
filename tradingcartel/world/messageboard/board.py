"""The message board: one shared board, where every post is broadcast to all the other agents."""

from ...core.messages import ALL, Message


class BoardPost(Message):
    """An agent posted to the message board."""

    to: str | None = ALL
    text: str

    def describe(self) -> str:
        return f"{self.sender} posted on the message board: {self.text}"


class MessageBoard:
    """Keeps every post, in order."""

    def __init__(self) -> None:
        self.posts: list[BoardPost] = []

    def handle(self, message: Message) -> list[Message]:
        if isinstance(message, BoardPost):
            self.posts.append(message)
        return []
