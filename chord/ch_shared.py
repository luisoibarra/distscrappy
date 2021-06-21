import time
from shared.const import NS_TIME_RETRY, NS_TRY_AMOUNT
import Pyro4 as pyro
from Pyro4.errors import CommunicationError
import logging as log
from concurrent.futures import ThreadPoolExecutor,as_completed

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
    enter_time = time.time()
    ns = locate_ns(ns_addresses)
    object_uri = ns.lookup(name)
    ro = create_proxy(object_uri)
    try:
        ro._pyroTimeout = 10 # Wait two seconds
        ro._pyroBind() # Check if the remote object is alive
    except CommunicationError as exc:
        exc_time = time.time()
        log.warning(f"TEMPORARY REMOVING NAME {name}. DELAY {exc_time - enter_time}")
        remove_name_from_ns(name, ns_addresses, object_uri)
        rem_time = time.time()
        log.warning(f"TEMPORARY REMOVED NAME {name}. DELAY {rem_time - exc_time}")
        raise exc
    except TimeoutError as exc:
        log.error("TIMEOUTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT")
        log.exception(exc)
    except Exception:
        exc_time = time.time()
        log.warning(f"TEMPORARY FUNCTION TEST FOR CREATING PROXY {name}. DELAY {exc_time - enter_time}")
    return ro

def remove_name_from_ns(name:str, ns_addresses: list, current_value=None):
    """
    Remove given name from name servers located at ns_addresses.  
    
    if current_value is given then the value in the name server must be equal in order to 
    remove the name 
    """
    ns_addresses = ns_addresses.copy()
    while ns_addresses:
        addr = ns_addresses.pop()
        try:
            with locate_ns([addr]) as ns:
                if current_value:
                    value = ns.lookup(name)
                    if value != current_value:
                        continue
                ns.remove(name)
        except Exception as exc:
            log.debug(f"Error removing {name} name server located at {addr}. {exc}")
            
def locate_ns(ns_addresses: list, amounts:int=NS_TRY_AMOUNT, retry_time:int=NS_TIME_RETRY)->pyro.Proxy:
    """
    Returns a responding name server among the ns_addresses
    """
    while amounts > 0:
        exceptions = []
        tasks=[]
           
        with ThreadPoolExecutor() as executor:
            tasks = [executor.submit(pyro.locateNS, ns_host, ns_port)for ns_host, ns_port in ns_addresses]
            for task in as_completed(tasks):
                try:
                    ns=task.result()
                    if not ns is None:
                        ns.ping() # Check if it is alive
                        return ns
                except Exception as exc:
                    exceptions.append(exc)
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
    
