from functools import reduce

from Pyro4.core import Proxy
from shared.const import IP_DIR
from config import CLOCK_SYNC_DELAY_SECONDS
from typing import Dict, List, Union
from server.ring import RingNode
import time
from shared.logger import LoggerMixin
import Pyro4 as pyro
from concurrent.futures import ThreadPoolExecutor, as_completed
from shared.utils import wait
from chord.ch_shared import create_object_proxy, create_proxy, locate_ns


class TimeSynchronization(LoggerMixin):
    def __init__(self) -> None:
        super().__init__()
        self.running = False
        self.ns_cache = {}
        
    
    def startRecieveingClockTime(self, node:Proxy, client_data:Dict[float, Dict[str,Union[float,Proxy]]]):
        '''
        receive clock time from a connected client
        '''
        # recieve clock time
        try:
            clock_time = node.getClockTime()

            clock_time_diff = time.time() - clock_time

            client_data[node.id] = {"clock_time": clock_time,"time_difference": clock_time_diff,"remote_node": node}
        except Exception as e:
            self.log_exception(e)



    def startConnecting(self, ns_addresses: List[IP_DIR], executor:ThreadPoolExecutor=None):
        ''' 
        master thread function used to open portal for
        accepting clients over given port
        '''

        if executor is None:
            executor = ThreadPoolExecutor()

        self.running = True
        # fetch clock time at slaves / clients
        while self.running:
            # datastructure used to store client id and clock data
            client_data:Dict[float, Dict[str,Union[float,Proxy]]] = {}
            
            try:
                with locate_ns(ns_addresses) as ns:
                    availables = ns.list(prefix = RingNode.CHORD_NODE_PREFIX)

                tasks = []
                for client_name , client_address in availables.items():
                    try:
                        node:Proxy = create_object_proxy(client_name, ns_addresses, self.ns_cache)
                    except pyro.errors.PyroError as exc:
                        self.log_info(f"Error creating proxy for {client_name}")
                        continue
                    tasks.append(executor.submit(self.startRecieveingClockTime, node,client_data))
                
                # wait(tasks,return_when=ALL_COMPLETED)  # WAIT DOESN'T WORK, NO FUNCIONA
                # wait(tasks)
                for task in as_completed(tasks):
                    self.log_debug("Timing task completed")

                self.synchronizeAllClocks(client_data)
            except Exception as e:
                self.log_exception(e)
            time.sleep(CLOCK_SYNC_DELAY_SECONDS)
                    
    def stop(self):
        """
        Stops service
        """
        self.running = False

    # subroutine function used to fetch average clock difference
    def getAverageClockDiff(self, client_data:Dict[float, Dict[str,Union[float,Proxy]]]):

        time_difference_list = [client['time_difference'] for id, client in client_data.items()]

        sum_of_clock_difference = sum(time_difference_list)

        average_clock_difference = sum_of_clock_difference/len(client_data)

        return average_clock_difference


    def synchronizeAllClocks(self,client_data:Dict[float, Dict[str,Union[float,Proxy]]]):
        ''' 
        master sync thread function used to generate
        cycles of clock synchronization in the network 
        '''
        if len(client_data) > 0:

            average_clock_difference = self.getAverageClockDiff(client_data)

            for n_id,node in client_data.items():
                try:
                    synchronized_time = time.time() + average_clock_difference
                    self.log_debug(f"Clock sync node:Proxy {n_id} {average_clock_difference}")
                    node['remote_node'].setClockTime(synchronized_time)
                except Exception as e:
                    self.log_exception(e)

