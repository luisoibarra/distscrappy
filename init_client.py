"""
Start a DistscrappyClient connected to specified server in config.py
"""
from client.client import DistcrappyClient
import logging as log
from config import *


def start():
    log.basicConfig(level=log.DEBUG)
    client = DistcrappyClient([x for x,_,_ in SERVER_NS_ZMQ_ADDRS])
    client.start()
    
if __name__ == "__main__":
    start()