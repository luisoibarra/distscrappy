from functools import reduce
from typing import Dict
from server.ring import RingNode
import time
from shared.logger import LoggerMixin
import Pyro4 as pyro
from concurrent.futures import ThreadPoolExecutor
from chord.ch_shared import create_proxy


class TimeSynchronization(LoggerMixin):
    def __init__(self) -> None:
        super().__init__()
        # datastructure used to store client address and clock data
        self.client_data:Dict[float,object]= {}
        
    
    
    def startRecieveingClockTime(self,node):
        '''
        receive clock time from a connected client
        '''
        # recieve clock time
        try:
            clock_time = node.getClockTime()

            clock_time_diff = time.time() - clock_time

            self.client_data[node.id] = {"clock_time": clock_time,"time_difference": clock_time_diff,"remote_node": node}
        except Exception as e:
            pass



    def startConnecting(self, name_server_host, name_server_port, executor:ThreadPoolExecutor=None):
        ''' 
        master thread function used to open portal for
        accepting clients over given port
        '''
        if executor is None:
            executor = ThreadPoolExecutor()

        # fetch clock time at slaves / clients
        while True:

            with pyro.locateNS(name_server_host, name_server_port) as ns:
                availables = ns.list(prefix = RingNode.CHORD_NODE_PREFIX)

            for client_name , client_address in availables.items():
                node = create_proxy(client_address)
                current_thread = executor.submit(self.startRecieveingClockTime,node)
            self.synchronizeAllClocks()

            time.sleep(5)
                    


    # subroutine function used to fetch average clock difference
    def getAverageClockDiff(self):

        time_difference_list = [client['time_difference'] for id, client in self.client_data.items()]

        sum_of_clock_difference = sum(time_difference_list)

        average_clock_difference = sum_of_clock_difference/len(self.client_data)

        return average_clock_difference


    
    def synchronizeAllClocks(self):
        ''' 
        master sync thread function used to generate
        cycles of clock synchronization in the network 
        '''
        if len(self.client_data) > 0:

            average_clock_difference = self.getAverageClockDiff()

            for n_id,node in self.client_data.items():
                try:
                    synchronized_time = time.time() + average_clock_difference
                    node['remote_node'].setClockTime(synchronized_time)
                except Exception as e:
                    pass

