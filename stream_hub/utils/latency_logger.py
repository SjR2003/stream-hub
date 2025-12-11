import time
import logging
from functools import wraps

logging.getLogger(__name__)

def measure_latency(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        latency_ms = (end - start) * 1000
        print(f"[Latency] {func.__name__} executed in {latency_ms:.3f} ms")

        return result

    return wrapper
