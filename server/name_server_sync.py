from chord.ch_shared import locate_ns
from os import times
from typing import Dict, List, Tuple
from shared.logger import LoggerMixin
from shared.const import *
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from shared.utils import wait
import random
import time
import Pyro4 as pyro
from Pyro4.errors import PyroError

class NSSync(LoggerMixin):
    """
    Updates name server replicating info.
    """
    
    def __init__(self, name_servers: List[IP_DIR]):
        self.name_servers = name_servers
        self.running = False
        
        
    def start(self):
        """
        Starts the name server synchronization process
        """
        executor = ThreadPoolExecutor()
        
        sleep_time = 5
        self.running = True
        while self.running:
            tasks:List[Future] = []
            addresses = {}
            addresses_per_ns = {}
            
            for ns_addr in self.name_servers: # Fetch all name server data
                tasks.append(executor.submit(self.get_ns_items, ns_addr))
            
            # futures.wait(tasks, return_when=futures.ALL_COMPLETED) # WAIT DOESN'T WORK, NO FUNCIONA
            # wait(tasks)
            for task in as_completed(tasks):
                try:
                    result = ns_addr, ns_addresses = task.result()
                    if result:
                        addresses.update(ns_addresses)
                        addresses_per_ns[ns_addr] = ns_addresses
                except Exception as exc:
                    self.log_exception(exc)
                
            tasks.clear()
            
            for ns_addr in self.name_servers: # Update name server data
                tasks.append(executor.submit(self.update_ns, ns_addr, addresses_per_ns.get(ns_addr,{}), addresses))

            # futures.wait(tasks, return_when=futures.ALL_COMPLETED) # WAIT DOESN'T WORK, NO FUNCIONA
            # wait(tasks)
            for task in as_completed(tasks):
                if task.exception():
                    self.log_debug(f"Name server task finished with an error. {task.exception()}")
                else:
                    self.log_debug("Name server task finished.")
                
            tasks.clear()
            
            for ns_addr in addresses_per_ns:
                self.log_debug(f"Name Server: {ns_addr} has {addresses_per_ns[ns_addr]}")
            
            time.sleep(sleep_time)

        executor.shutdown()
    
    def get_ns_items(self, ns_addr:IP_DIR)-> Tuple[IP_DIR,Dict[str,str]]:
        """
        Returns the items from given name server
        """
        host, port = ns_addr
        self.log_debug(f"Fetching data from ns {host}:{port}")
        try:
            with locate_ns([(host, port)]) as ns:
                ns_addresses = ns.list()
            pyro_ns_name = "Pyro.NameServer"
            if pyro_ns_name in ns_addresses:
                ns_addresses.__delitem__(pyro_ns_name)
            return ns_addr, ns_addresses
        except PyroError as e:
            self.log_info(f"Name server {host}:{port} {e}")    
            return None, None
    
    def update_ns(self, ns_addr: IP_DIR, ns_items: Dict[str,str], addresses: Dict[str,str]):
        """
        Update the given name server with given addresses
        """
        host, port = ns_addr
        self.log_debug(f"Updating data to ns {host}:{port}")
        try:
            with locate_ns([(host, port)]) as ns:
                for name,uri in addresses.items():
                    # Check if ns has the key
                    ns_saved_uri = ns_items.get(name, None) 
                    if not ns_saved_uri:
                        ns.register(name,uri)
                    # TODO Check for posibles repeated names with different URIs
        except PyroError as e:
            self.log_info(f"Name server {host}:{port} {e}")
    
    def stop(self):
        """
        Stops the name server synchronization process
        """
        self.running = False