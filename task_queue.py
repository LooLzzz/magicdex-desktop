from threading import Thread
from queue import Queue

class TaskQueue(Queue):
    def __init__(self, num_workers=5):
        Queue.__init__(self)
        self.num_workers = num_workers
        self.start_workers()

    def start_workers(self):
        for _i in range(self.num_workers):
            t = Thread(target=self.worker)
            t.daemon = True
            t.start()

    def worker(self):
        while True:
            [item, args, kwargs] = self.get()
            item(*args, **kwargs)
            self.task_done()
    
    def add_task(self, task, *args, **kwargs):
        args = args or ()
        kwargs = kwargs or {}
        self.put([task, args, kwargs])


# def tests():
#     def blokkah(*args, **kwargs):
#         time.sleep(5)
#         print "Blokkah mofo!"

#     q = TaskQueue(num_workers=5)

#     for item in range(10):
#         q.add_task(task=blokkah)

#     q.join()       # block until all tasks are done
#     print "All done!"

# if __name__ == "__main__":
#     tests()