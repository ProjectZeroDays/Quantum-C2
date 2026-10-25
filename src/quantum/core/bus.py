"""quantum.core.bus — Event bus (SSE + WS) for real-time UI updates.

Provides pub/sub event bus with SSE transport for the RAT dashboard.
No polling: everything in the UI is a subscriber.

Requires an asyncio event loop context for subscriber management.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from asyncio import Queue, wait_for as asyncio_wait_for
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import threading


@dataclass
class Event:
    """An event published on the bus."""
    topic: str
    data: Dict[str, Any]
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.event_id,
            "topic": self.topic,
            "data": self.data,
            "timestamp": self.timestamp,
        }

    def to_sse(self) -> str:
        """Format as Server-Sent Event."""
        data = self.to_dict()
        return f"id: {self.event_id}\ndata: {json.dumps(data)}\n\n"


class EventBus:
    """Pub/sub event bus with SSE fan-out support."""

    def __init__(self):
        # subscriber_id -> {"topics": set|None, "queue": Queue|None, "active": bool}
        self._subscribers: Dict[str, Dict[str, Any]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._lock = threading.RLock()

    async def subscribe(self, subscriber_id: str, topics: Optional[set] = None):
        """Subscribe to events. topics=None subscribes to all."""
        with self._lock:
            self._subscribers[subscriber_id] = {
                "topics": topics,
                "queue": Queue(),
                "active": True,
            }
        return self._subscribers[subscriber_id]

    async def unsubscribe(self, subscriber_id: str):
        """Unsubscribe a subscriber."""
        with self._lock:
            self._subscribers.pop(subscriber_id, None)

    async def publish(self, topic: str, data: Dict[str, Any]) -> Event:
        """Publish an event to all matching subscribers."""
        event = Event(topic=topic, data=data)

        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
            for sub in self._subscribers.values():
                if not sub.get("active"):
                    continue
                sub_topics = sub.get("topics")
                if sub_topics is not None and topic not in sub_topics:
                    continue
                q = sub.get("queue")
                if q is None:
                    continue
                try:
                    q.put_nowait(event)
                except Exception:
                    sub["active"] = False

        return event

    async def subscribe_stream(self, subscriber_id: str, topics: Optional[set] = None):
        """Async generator yielding events for a subscriber (SSE/WS handler)."""
        sub = await self.subscribe(subscriber_id, topics)
        try:
            while sub.get("active", True):
                q = sub.get("queue")
                if q is None:
                    break
                try:
                    event = await asyncio_wait_for(q.get(), timeout=30.0)
                    yield event
                except asyncio.TimeoutError:
                    yield Event(topic="heartbeat", data={"alive": True})
                except asyncio.CancelledError:
                    break
        finally:
            await self.unsubscribe(subscriber_id)

    def get_history(self, topic: str = None, limit: int = 100) -> List[Event]:
        """Get recent event history, optionally filtered by topic."""
        with self._lock:
            events = list(self._event_history)
        if topic:
            events = [e for e in events if e.topic == topic]
        return events[-limit:]

    def stats(self) -> Dict[str, Any]:
        """Get bus statistics."""
        with self._lock:
            topic_counts: Dict[str, int] = {}
            for event in self._event_history:
                topic_counts[event.topic] = topic_counts.get(event.topic, 0) + 1
            return {
                "subscribers": len(self._subscribers),
                "total_events": len(self._event_history),
                "topic_counts": topic_counts,
                "max_history": self._max_history,
            }


# Global event bus instance
_bus: Optional[EventBus] = None


def get_bus() -> EventBus:
    """Get or create the global event bus instance."""
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus


async def publish(topic: str, data: Dict[str, Any]) -> Event:
    """Publish an event using the global bus."""
    return await get_bus().publish(topic, data)


async def subscribe(subscriber_id: str, topics: Optional[set] = None):
    """Subscribe to events using the global bus."""
    return await get_bus().subscribe(subscriber_id, topics)


async def subscribe_stream(subscriber_id: str, topics: Optional[set] = None):
    """Async generator for a subscriber using the global bus."""
    async for event in get_bus().subscribe_stream(subscriber_id, topics):
        yield event
