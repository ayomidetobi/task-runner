"""Logging events to Redis."""
from .parse import to_dict
from redis.asyncio import Redis as AsyncRedis
from redis import Redis
from .event import Event


class EventStore:
    """Class that handles logging events to Redis."""

    def __init__(self, stream_key: str):
        self.stream_key = stream_key

    async def log(self, r: AsyncRedis, event: Event):
        return await r.xadd(self.stream_key, to_dict(event))

    def log_sync(self, r: Redis, event: Event):
        return r.xadd(self.stream_key, to_dict(event))
