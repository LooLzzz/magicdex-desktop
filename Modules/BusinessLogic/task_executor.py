import time
from concurrent.futures import ThreadPoolExecutor


class TaskExecutor(ThreadPoolExecutor):
    '''
    A class for executing multi-threaded tasks.
    '''
    def __init__(self, max_workers=5, delay=None, callback=None):
        '''
        `max_workers` max number of workers for the task pool.\n
        `delay` (optional) delay in seconds between tasks.
        '''
        super().__init__(max_workers)
        self._delay = delay
        self.callback = callback
        self.futures = []

    def _delayed(self, func, delay=None):
        '''
        A wrapper for delaying the start of each task (if needed).\n
        Shouldn't be used outside of this class.
        '''
        delay = delay or self._delay
        def wrapper(*args, **kwargs):
            res = func(*args, **kwargs)
            if delay != None:
                time.sleep(delay)
            return res
        return wrapper

    def submit(self, task, delay=None, *args, **kwargs):
        '''
        Add a task to the task pool.\n
        ---
        `task` the task which the workers shoudl complete, `*args` and `**kwargs` will be passed to it.\n
        `delay` (optional) delay in seconds between tasks.
        '''
        delayed_task = self._delayed(task, delay)
        res = super().submit(fn=delayed_task, *args, **kwargs)
        self.futures += [res]
        # self.futures.append(res)
        return res