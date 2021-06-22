import time
from shared.const import IP_DIR, NS_TIME_RETRY, NS_TRY_AMOUNT
import Pyro4 as pyro
from Pyro4.errors import CommunicationError
import logging as log
from concurrent.futures import ThreadPoolExecutor,as_completed
from typing import List, Dict

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
        
def create_object_proxy(name, ns_addresses: List[IP_DIR], ns_cache: Dict[str, URI]=None):
    """
    Create an object proxy from the given name 
    """
    
    if ns_cache is None:
        ns_cache = {}

    cache_used = True
    object_uri = ns_cache.get(name, None)
    if not object_uri:    
        ns = locate_ns(ns_addresses)
        object_uri = ns.lookup(name)
        cache_used = False
    ro = create_proxy(object_uri)
    
    try:
        ro._pyroTimeout = 64 # Wait seconds
        ro._pyroBind() # Check if the remote object is alive
    except CommunicationError as exc:
        ns_cache.pop(name, None)
        log.debug(f"NS Cache removed {name}")
        if not cache_used:
            remove_name_from_ns(name, ns_addresses, object_uri)
            log.warning(f"NS Name removed {name}")
            raise exc
        next_dict: Dict[str, URI] = {}
        ro = create_object_proxy(name, ns_addresses, next_dict)
        log.debug(f"NS Cache updated {next_dict}")
        ns_cache.update(next_dict)
    except TimeoutError as exc:
        log.warning(f"Remote object {name} timeout")
        log.exception(exc)
    except Exception as exc:
        log.exception(exc)
    if not cache_used:
        ns_cache[name] = object_uri
        log.debug(f"NS Cache updated {name}")
    else:
        log.debug(f"NS Cache hit {name}")
    return ro

def remove_name_from_ns(name:str, ns_addresses: List[IP_DIR], current_value=None):
    """
    Remove given name from name servers located at ns_addresses.  
    
    if current_value is given then the value in the name server must be equal in order to 
    remove the name 
    """
    ns_addresses = ns_addresses.copy()
    def remove_name_from_single_ns(addr):
        try:
            with locate_ns([addr]) as ns:
                if current_value:
                    value = ns.lookup(name)
                    if value != current_value:
                        return
                ns.remove(name)
        except Exception as exc:
            log.debug(f"Error removing {name} name server located at {addr}. {exc}")
                    
    with ThreadPoolExecutor() as executor:
        tasks = [executor.submit(remove_name_from_single_ns, addr) for addr in ns_addresses]
        for t in as_completed(tasks):
            log.debug(f"Removing {name} from NS task finished")
    
            
def locate_ns(ns_addresses: List[IP_DIR], amounts:int=NS_TRY_AMOUNT, retry_time:int=NS_TIME_RETRY)->pyro.Proxy:
    """
    Returns a responding name server among the ns_addresses
    """
    while amounts > 0:
        exceptions = []
           
        executor = ThreadPoolExecutor()
        tasks = [executor.submit(pyro.locateNS, ns_host, ns_port)for ns_host, ns_port in ns_addresses]
        for task in as_completed(tasks):
            try:
                ns=task.result()
                if not ns is None:
                    ns.ping() # Check if it is alive
                    executor.shutdown(False)
                    return ns
            except Exception as exc:
                exceptions.append(exc)
        executor.shutdown(False)
        try:
            raise exceptions[0]
        except pyro.errors.PyroError as exc:
            log.info(
                f"Can't locate the name servers {ns_addresses}. Retrying in {retry_time} seconds...")
            time.sleep(retry_time)
            amounts -= 1

    raise CommunicationError("Failed to locate name servers")

def create_proxy(dir:URI)->pyro.Proxy:
    """
    Create an object proxy from the given dir
    """
    return pyro.Proxy(dir)
    
