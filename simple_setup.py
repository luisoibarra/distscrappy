"""
Start a simple Distscrappy network based on config.py
"""

from server.central import CentralNode
from server.ring import RingNode
from client.client import DistcrappyClient
from concurrent.futures import ThreadPoolExecutor
import time
import logging as log
import init_central as ic
import simple_rings as sr
import init_client as icl
from config import *

def start():

    log.basicConfig(level=log.INFO)

    executor = ThreadPoolExecutor()

    central_task = executor.submit(ic.start)

    time.sleep(.5)
    
    rings_task = executor.submit(sr.start)
    
    # time.sleep(5)
    # result = client.get_urls(["http://127.0.0.5:9000"])
    # print(result)
    print(central_task.result())

if __name__ == "__main__":
    start()