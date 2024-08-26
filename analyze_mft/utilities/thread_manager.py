import concurrent.futures
from threading import Lock

class ThreadManager:
    def __init__(self, thread_count):
        self.thread_count = max(1, thread_count)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.thread_count)
        self.lock = Lock()

    def map(self, func, iterable):
        return list(self.executor.map(func, iterable))

    def submit(self, func, *args, **kwargs):
        return self.executor.submit(func, *args, **kwargs)

    def safe_increment(self, value):
        with self.lock:
            value += 1
        return value

    def shutdown(self):
        self.executor.shutdown(wait=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()