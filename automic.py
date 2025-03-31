import threading
from dataclasses import dataclass


@dataclass(slots=True)
class AtomicCounter:
    value: int = 0
    _lock: threading.Lock = threading.Lock()

    def increment(self) -> int:
        with self._lock:
            self.value += 1
            return self.value

    def decrement(self) -> int:
        with self._lock:
            self.value -= 1
            return self.value

    def get(self) -> int:
        with self._lock:
            return self.value

# 全局实例
global_counter = AtomicCounter()
