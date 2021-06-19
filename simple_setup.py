"""
Start a simple Distscrappy network based on config.py
"""

from server.central import CentralNode
from server.ring import RingNode
from client.client import DistScrappyClient
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures as conc
import time
import logging as log
import simple_centrals as scs
import simple_rings as sr
from config import *
import init_storage as st 

def start():

    log.basicConfig(level=log.INFO)

    executor = ProcessPoolExecutor()

    central_task = executor.submit(scs.start)

    time.sleep(5)
    
    rings_task = executor.submit(sr.start)
    
    storage_task = executor.submit(st.start)
    # time.sleep(5)
    # result = client.get_urls(["http://127.0.0.5:9000"])
    # print(result)
    for task in conc.as_completed([central_task, rings_task, storage_task]):
        print("Task finished")

if __name__ == "__main__":
    start()