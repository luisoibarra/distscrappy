"""
Start a Storage Node using address in config.py
"""

from shared.const import IP_DIR, SERV_NS
from server.storage import StorageNode
import logging as log
from config import *

def start(
    address:('address','option','addr',str) = None,
    *ns_addresses:('name server addresses','option',str)
    ):
    log.basicConfig(level=log.DEBUG)
    if address is None:
        host, port = STORAGE_ADDR
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
    storage = StorageNode(ns_addresses, (host, port))
    storage.start()
    
if __name__ == "__main__":
    import plac
    plac.call(start)

