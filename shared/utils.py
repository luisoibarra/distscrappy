import time
from concurrent.futures import Future
from typing import List

def wait(tasks: List[Future], timeout=None):
    """
    Wait until all tasks are done
    """
    # current = time.time()
    while not all(x.done() for x in tasks):
        time.sleep(.3)
        # if timeout:
        #     if time.time() - current > timeout:
        #         break
    