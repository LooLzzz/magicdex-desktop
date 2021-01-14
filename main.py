import pandas as pd
import fetch_data as fetch
from task_queue import TaskQueue

if __name__ == "__main__":
    sets = ['m10','m11','m12']
    
    q = TaskQueue(num_workers=len(sets))
    for s in sets:
        q.add_task(fetch.fetch_card_images, set_id=s, num_workers=25)
    q.join()