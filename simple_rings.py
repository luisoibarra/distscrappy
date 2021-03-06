"""
Start a simple Ring Node topology using addresses in config.py
"""

from server.central import CentralNode
from server.ring import RingNode
from client.client import DistScrappyClient
from concurrent.futures import ThreadPoolExecutor
import time
import logging as log
import init_ring as ir
from config import *


def start():
    log.basicConfig(level=log.INFO)

    executor = ThreadPoolExecutor()

    ring_tasks = []
    for i in range(len(RING_ADDRS)):
        time.sleep(2)
        ring_task = executor.submit(ir.start,i)
        ring_tasks.append(ring_task)
        time.sleep(16)
    for t in ring_tasks:
        print(t.result())
            
if __name__ == "__main__":
    start()
