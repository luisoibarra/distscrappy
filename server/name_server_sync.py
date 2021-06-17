from chord.ch_shared import locate_ns
from os import times
from typing import Dict, List
from shared.logger import LoggerMixin
from shared.const import *
from concurrent.futures import ThreadPoolExecutor, Future
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
        
        sleep_time = 5
        self.running = True
        while self.running:
            addresses = {}
            addresses_per_ns = {}
            for host,port in self.name_servers: # Fetch all name server data
                self.log_debug(f"Fetching data from ns {host}:{port}")
                try:
                    with locate_ns([(host, port)]) as ns:
                        ns_addresses = ns.list()
                    pyro_ns_name = "Pyro.NameServer"
                    if pyro_ns_name in ns_addresses:
                        ns_addresses.__delitem__(pyro_ns_name)
                    addresses.update(ns_addresses)
                    addresses_per_ns[(host,port)] = ns_addresses
                except PyroError as e:
                    self.log_info(f"Name server {host}:{port} {e.args[0]}")

            for host,port in self.name_servers: # Update name server data
                self.log_debug(f"Updating data to ns {host}:{port}")
                try:
                    with locate_ns([(host, port)]) as ns:
                        for name,uri in addresses.items():
                            # Check if ns has the key
                            ns_saved_uri = addresses_per_ns[(host,port)].get(name, None) 
                            if not ns_saved_uri:
                                ns.register(name,uri)
                            # TODO Check for posibles repeated names with different URIs
                except PyroError as e:
                    self.log_info(f"Name server {host}:{port} {e.args[0]}")
            
            time.sleep(sleep_time)
            
    def stop(self):
        """
        Stops the name server synchronization process
        """
        self.running = False