from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from part4_oop.interfaces import Cache, HasCache, Policy, Storage

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class DictStorage(Storage[K, V]):
    _data: dict[K, V] = field(default_factory=dict, init=False)

    def set(self, key: K, value: V) -> None:
        self._data[key] = value

    def get(self, key: K) -> V | None:
        return self._data.get(key)

    def exists(self, key: K) -> bool:
        return key in self._data

    def remove(self, key: K) -> None:
        if key in self._data:
            del self._data[key]

    def clear(self) -> None:
        self._data.clear()


@dataclass
class LRUPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)

    def get_key_to_evict(self) -> K | None:
        if len(self._order) > self.capacity:
            return self._order[0]
        return None

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return len(self._order) > 0


@dataclass
class FIFOPolicy(Policy[K]):
    capacity: int = 5
    _order: list[K] = field(default_factory=list, init=False)

    def register_access(self, key: K) -> None:
        if key not in self._order:
            self._order.append(key)

    def get_key_to_evict(self) -> K | None:
        if len(self._order) > self.capacity:
            return self._order[0]
        return None

    def remove_key(self, key: K) -> None:
        if key in self._order:
            self._order.remove(key)

    def clear(self) -> None:
        self._order.clear()

    @property
    def has_keys(self) -> bool:
        return len(self._order) > 0


@dataclass
class LFUPolicy(Policy[K]):
    capacity: int = 5
    _key_counter: dict[K, int] = field(default_factory=dict, init=False)
    _last_key: K | None = field(default=None, init=False)

    def register_access(self, key: K) -> None:
        self._last_key = key  # запомнили ластовый ключ
        count = 1 + self._key_counter.get(key, 0)
        if key in self._key_counter:
            del self._key_counter[key]
        self._key_counter[key] = count

    def get_key_to_evict(self) -> K | None:
        if len(self._key_counter) <= self.capacity:
            return None
        candidaty = {key: value for key, value in self._key_counter.items() if key != self._last_key}  # мб вылетающие

        if not candidaty:
            return self._last_key
        return min(candidaty, key=lambda k: candidaty[k])

    def remove_key(self, key: K) -> None:
        if key in self._key_counter:
            del self._key_counter[key]

    def clear(self) -> None:
        self._key_counter.clear()

    @property
    def has_keys(self) -> bool:
        return len(self._key_counter) > 0


class MIPTCache(Cache[K, V]):
    def __init__(self, storage: Storage[K, V], policy: Policy[K]) -> None:
        self.storage = storage
        self.policy = policy

    def set(self, key: K, value: V) -> None:
        self.storage.set(key, value)
        self.policy.register_access(key)
        maby_evict_key = self.policy.get_key_to_evict()
        if maby_evict_key is not None:
            self.storage.remove(maby_evict_key)
            self.policy.remove_key(maby_evict_key)

    def get(self, key: K) -> V | None:
        if self.storage.exists(key):
            self.policy.register_access(key)
            return self.storage.get(key)
        return None

    def exists(self, key: K) -> bool:
        return self.storage.exists(key)

    def remove(self, key: K) -> None:
        self.storage.remove(key)
        self.policy.remove_key(key)

    def clear(self) -> None:
        self.storage.clear()
        self.policy.clear()


class CachedProperty[V]:
    def __init__(self, func: Callable[..., V]) -> None:
        self.func = func
        self.attr_name = f"_cached_{func.__name__}"

    def __get__(self, instance: HasCache[Any, Any] | None, owner: type) -> Any:
        if instance is None:
            return self
        cache = instance.cache
        cached_value: None | V = cache.get(self.attr_name)
        if cached_value is None:
            result = self.func(instance)
            cache.set(self.attr_name, result)
            return result
        return cached_value
