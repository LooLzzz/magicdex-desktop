from threading import Thread
from queue import Queue

class TaskQueue(Queue):
    def __init__(self, num_workers=5, run=False):
        Queue.__init__(self)
        self.num_workers = num_workers
        self.workers = []
        self.init_workers(run)

    def init_workers(self, run):
        for _i in range(self.num_workers):
            t = Thread(target=self.worker)
            t.daemon = True
            self.workers += [t]
            if run:
                t.start()

    def join(self):
        """
        This method will start the workers (if they haven't started already) and join them
        """
        for t in self.workers:
            if not t.is_alive():
                t.start()
        super().join()

    def worker(self):
        while True:
            [item, args, kwargs] = self.get()
            item(*args, **kwargs)
            self.task_done()

    def add_task(self, task, *args, **kwargs):
        args = args or ()
        kwargs = kwargs or {}
        self.put([task, args, kwargs])