import time
from concurrent.futures import ThreadPoolExecutor

class TaskExecutor(ThreadPoolExecutor):
    def __init__(self, max_workers=5, delay=None):
        super().__init__(max_workers)
        self.delay = delay
        self.futures = []

    def delayed(self, func, delay=None):
        delay = delay or self.delay
        def wrapper(*args, **kwargs):
            res = func(*args, **kwargs)
            if delay != None:
                time.sleep(delay)
            return res
        return wrapper

    def submit(self, task, delay=None, *args, **kwargs):
        delayed_task = self.delayed(task, delay)
        res = super().submit(fn=delayed_task, *args, **kwargs)
        self.futures += [res]
        return res