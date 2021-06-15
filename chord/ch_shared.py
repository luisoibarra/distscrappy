import Pyro4 as pyro
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
        
def create_object_proxy(name, ns_host:str, ns_port:int):
    """
    Create an object proxy from the given name 
    """
    with pyro.locateNS(ns_host, ns_port) as ns:
        object_uri = ns.lookup(name)
        return pyro.Proxy(object_uri)

def create_proxy(dir:URI)->pyro.Proxy:
    """
    Create an object proxy from the given dir
    """
    return pyro.Proxy(dir)
    
