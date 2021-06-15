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
import plac

def start(
    index:('index','option','i',int) = 0,
    address:('address','option','addr',str) = None
    ):
    log.basicConfig(level=log.INFO)
    if address is None:
        host, port = RING_ADDRS[index]
    else:
        host,port=address.split(":")
    ring = RingNode(host, int(port), NS_ADDR[0], NS_ADDR[1])
    ring.start()
    
if __name__ == "__main__":
    import plac
    plac.call(start)

