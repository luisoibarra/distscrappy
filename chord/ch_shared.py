import time
from shared.const import NS_TIME_RETRY, NS_TRY_AMOUNT
import Pyro4 as pyro
from Pyro4.errors import CommunicationError
import logging as log

from Pyro4.core import Proxy, URI

def method_logger(fun):
    """
    Decorator for logging methods calls
    """
    def ret_fun(*args, **kwargs):
        log.debug(f"{fun.__name__} called with {args[1:]} and {kwargs}")
        try:
            value = fun(*args, **kwargs)
        except Exception as exc:
            log.exception(exc)
            raise exc
        log.debug(f"{fun.__name__} exited returning {value}")
        return value
    return ret_fun
        
def create_object_proxy(name, ns_addresses: list):
    """
    Create an object proxy from the given name 
    """
    ns = locate_ns(ns_addresses)
    object_uri = ns.lookup(name)
    return pyro.Proxy(object_uri)

def locate_ns(ns_addresses: list):
    amounts = NS_TRY_AMOUNT
    while amounts > 0:
        exceptions = []
        for ns_host, ns_port in ns_addresses:
            try:
                ns = pyro.locateNS(ns_host, ns_port)
                ns.ping() # Check if it is alive
                return ns
            except Exception as exc:
                exceptions.append(exc)
        try:
            raise exceptions[0]
        except pyro.errors.PyroError:
            log.info(
                f"Can't locate a name servers... retrying in {NS_TIME_RETRY} seconds...")
            time.sleep(NS_TIME_RETRY)
            amounts -= 1
    else:
        raise CommunicationError("Failed to locate name servers")

def create_proxy(dir:URI)->pyro.Proxy:
    """
    Create an object proxy from the given dir
    """
    return pyro.Proxy(dir)
    
