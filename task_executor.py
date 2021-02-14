import time
from concurrent.futures import ThreadPoolExecutor

class TaskExecutor(ThreadPoolExecutor):
    def __init__(self, max_workers=5, delay=None):
        super().__init__(max_workers)
        self._delay = delay
        self.futures = []

    def _delayed(self, func, delay=None):
        delay = delay or self._delay
        def wrapper(*args, **kwargs):
            res = func(*args, **kwargs)
            if delay != None:
                time.sleep(delay)
            return res
        return wrapper

    def submit(self, task, delay=None, *args, **kwargs):
        delayed_task = self._delayed(task, delay)
        res = super().submit(fn=delayed_task, *args, **kwargs)
        self.futures += [res]
        return res