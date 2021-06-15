"""
Start a DistscrappyClient connected to specified server in config.py
"""
from server.central import CentralNode
from server.ring import RingNode
from client.client import DistcrappyClient
from concurrent.futures import ThreadPoolExecutor
import time
import logging as log
from config import *


def start():
    log.basicConfig(level=log.DEBUG)
    client = DistcrappyClient([CENTRAL_ADDR])
    client.start()
    
if __name__ == "__main__":
    start()