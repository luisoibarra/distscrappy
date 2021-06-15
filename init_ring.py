"""
Start a Ring Node using address in config.py
"""

from server.central import CentralNode
from server.ring import RingNode
from client.client import DistcrappyClient
from concurrent.futures import ThreadPoolExecutor
import time
import logging as log
from config import *


def start(index:int):
    log.basicConfig(level=log.DEBUG)
    host, port = RING_ADDRS[index]
    ring = RingNode(host, port, NS_ADDR[0], NS_ADDR[1])
    ring.start()
    
if __name__ == "__main__":
    index = 0
    start(index)

