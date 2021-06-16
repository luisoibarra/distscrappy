"""
Start a simple Central Node topology using addresses in config.py
"""

from concurrent.futures import ThreadPoolExecutor
import time
import logging as log
import init_central as ic
from config import *


def start():
    log.basicConfig(level=log.DEBUG)

    executor = ThreadPoolExecutor()

    central_tasks = []
    for i in range(len(SERVER_AND_NS_ADDRS)):
        time.sleep(.5)
        central_task = executor.submit(ic.start,i)
        central_tasks.append(central_task)
    for t in central_tasks:
        print(t.result())
            
if __name__ == "__main__":
    start()
