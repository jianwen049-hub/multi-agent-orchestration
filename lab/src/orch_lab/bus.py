"""In-process message bus with history for replay."""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Callable

from orch_lab.messages import Envelope


Handler = Callable[[Envelope], None]


class MessageBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[Handler]] = defaultdict(list)
        self._queue: deque[Envelope] = deque()
        self.history: list[Envelope] = []

    def subscribe(self, recipient: str, handler: Handler) -> None:
        self._subs[recipient].append(handler)

    def publish(self, envelope: Envelope) -> None:
        self.history.append(envelope)
        self._queue.append(envelope)

    def drain(self, max_n: int = 100) -> int:
        """Deliver queued messages to subscribers. Returns count delivered."""
        n = 0
        while self._queue and n < max_n:
            env = self._queue.popleft()
            for handler in self._subs.get(env.recipient, []):
                handler(env)
            n += 1
        return n

    def pending(self) -> int:
        return len(self._queue)
