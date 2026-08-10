from typing import Optional

class RedisMock:
    """A simple in-memory mock for Redis to allow testing without a Redis server."""
    _store = {}

    def setex(self, name: str, time: int, value: str):
        self._store[name] = value
        # In a real mock we would handle expiration, but for testing it's fine

    def get(self, name: str) -> Optional[bytes]:
        value = self._store.get(name)
        if value is None:
            return None
        return value.encode("utf-8") if isinstance(value, str) else value

    def delete(self, name: str):
        if name in self._store:
            del self._store[name]

    def ping(self) -> bool:
        return True
