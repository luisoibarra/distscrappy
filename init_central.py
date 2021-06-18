"""
Start a CentralNode based on config.py
"""
from server.central import CentralNode
import logging as log
from config import *
from shared.const import *
from typing import Tuple, List
import plac

def start(
    index:('index','option','i',int) = 0,
    central_address:('central address','option','c',str) = None,
    ns_address:('name server address','option','ns',str) = None,
    zmq_address:('zmq address','option','zmq',str) = None,
    addresses:('Server addresses','option','server',List[Tuple[IP_DIR,IP_DIR,IP_DIR]])=SERVER_NS_ZMQ_ADDRS
    ):
    log.basicConfig(level=log.DEBUG)
    if central_address is None or ns_address is None:
        central_addr, ns_addr, zmq_addr = SERVER_NS_ZMQ_ADDRS[index]
    else:
        central_host, central_port = central_address.split(":")
        ns_host, ns_port = ns_address.split(":")
        zmq_host, zmq_port = zmq_address.split(":")
        central_addr = (central_host, int(central_port))
        ns_addr = (ns_host, int(ns_port))
        zmq_addr = (zmq_host, int(zmq_port))
    central = CentralNode(ns_addr, central_addr, zmq_addr, [x for x in addresses if x != (central_addr, ns_addr, zmq_addr)])
    central.start()

if __name__ == "__main__":
    plac.call(start)
