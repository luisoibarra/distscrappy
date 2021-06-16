"""
Start a CentralNode based on config.py
"""
from server.central import CentralNode
from server.ring import RingNode
from client.client import DistcrappyClient
from concurrent.futures import ThreadPoolExecutor
import time
import logging as log
from config import *


def start(
    index:('index','option','i',int) = 0,
    central_address:('central address','option','addr',str) = None,
    ns_address:('name server address','option','addr',str) = None
    ):
    log.basicConfig(level=log.DEBUG)
    if central_address is None or ns_address is None:
        central_addr, ns_addr = SERVER_AND_NS_ADDRS[index]
    else:
        central_host, central_port = central_address.split(":")
        ns_host, ns_port = ns_address.split(":")
        central_addr = (central_host, int(central_port))
        ns_addr = (ns_host, int(ns_port))
    central = CentralNode(ns_addr, central_addr)
    central.start()

if __name__ == "__main__":
    start()
