"""
Start a Ring Node using address in config.py
"""

from shared.const import IP_DIR, SERV_NS
from typing import List
from server.central import CentralNode
from server.ring import RingNode
from client.client import DistScrappyClient
from concurrent.futures import ThreadPoolExecutor
import time
import logging as log
from config import *

def start(
    index:('index','option','i',int) = 0,
    address:('address','option','addr',str) = None,
    *ns_addresses:('name server addresses')
    ):
    log.basicConfig(level=log.INFO)
    if address is None:
        host, port = RING_ADDRS[index]
    else:
        host, port = address.split(":")
    if not ns_addresses:
        ns_addresses = [x[SERV_NS] for x in SERVER_NS_ZMQ_ADDRS]
    else:
        new_addresses = []
        for addr in ns_addresses:
            host,port = addr.split(":")
            new_addresses.append((host,int(port)))
        ns_addresses = new_addresses
    print(ns_addresses)
    ring = RingNode(host, int(port), bits=RING_BITS, ns_addresses=ns_addresses)
    ring.start()
    
if __name__ == "__main__":
    import plac
    plac.call(start)

