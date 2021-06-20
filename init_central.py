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
    *addresses:('Server addresses ordered Server, NS, ZMQ.')
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
    if addresses:
        if len(addresses) % 3 != 0:
            raise ValueError("Invalid number of addresses, must be a multiple of 3")
        server_addrs = [x.split(":") for i,x in enumerate(addresses) if i % 3 == 0]
        ns_addrs = [x.split(":") for i,x in enumerate(addresses) if i % 3 == 1]
        zmq_addrs = [x.split(":") for i,x in enumerate(addresses) if i % 3 == 2]
        addresses = [((host_server,int(port_server)), (host_ns,int(port_ns)), (host_zmq,int(port_zmq))) for (host_server,port_server), (host_ns, port_ns), (host_zmq, port_zmq) in zip(server_addrs, ns_addrs, zmq_addrs)]
    else:
        addresses = SERVER_NS_ZMQ_ADDRS
    central = CentralNode(ns_addr, central_addr, zmq_addr, [x for x in addresses if x != (central_addr, ns_addr, zmq_addr)])
    central.start()

if __name__ == "__main__":
    plac.call(start)
