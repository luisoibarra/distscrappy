from server.timing import TimeSynchronization
from shared.logger import LoggerMixin
from shared.const import *
import Pyro4 as pyro
from concurrent.futures import ThreadPoolExecutor, Future, CancelledError
from chord.ch_ns import init_name_server 
from server.ring import RingNode
from server.receiver import HTTPRequestReceiver
from chord.ch_shared import create_object_proxy
import random
from shared.error import DistscrappyError
import time

class CentralNode(LoggerMixin):
    """
    Central node that supports the name server and acts as client interface
    """
    
    def __init__(self, ns_address:IP_DIR, client_interface_address:IP_DIR):
        self.client_interface_address = client_interface_address
        self.ns_address = ns_address
        self.executor = ThreadPoolExecutor()
        self.receivers_tasks = None
        self.name_server_tasks = None
        self.timing_tasks = None
        self.running = False
    
    def start(self):
        """
        Start central node
        """
        self.name_server_tasks = []
        self.receivers_tasks = []
        self.timing_tasks = []

        ns_task = self.executor.submit(self.name_server_loop)
        self.name_server_tasks.append(ns_task)

        rec_task = self.executor.submit(self.receiver_server_loop)
        self.receivers_tasks.append(rec_task)

        time.sleep(1)
        
        ts = TimeSynchronization()
        host,port = self.ns_address
        time_task = self.executor.submit(ts.startConnecting(host,port,self.executor))
        self.timing_tasks.append(time_task)

        

        for ns_task in self.name_server_tasks:
            ns_task.add_done_callback(self._task_finish_callback("Name server"))
        for rec_task in self.receivers_tasks:
            rec_task.add_done_callback(self._task_finish_callback("Receiver"))

        self.running = True
        while self.running:
           time.sleep(1)
        
        self.log_info("Central Node Finished")

    def stop(self):
        """
        Stops the node
        """
        self.log_info("Stopping Central Node")
        self.log_debug("Cancelling tasks")
        for task in self.name_server_tasks + self.receivers_tasks:
            task.cancel()
        self.log_debug("Shutting down executor")
        self.executor.shutdown()
        self.log_debug("Executor is shutdown")
        self.running = False


    def _task_finish_callback(self, task_name:str):
        """
        Return a callback for finished tasks
        """
        def callback(task:Future):
            try:
                exc = task.exception(0)
                if exc:
                    self.log_exception(exc)
            except TimeoutError:
                pass
            except CancelledError:
                pass
            self.log_info(f"{task_name} finish")
        return callback
    
    def get_name_server(self):
        """
        Returns a name server proxy
        """
        return pyro.locateNS(self.ns_address[0], self.ns_address[1])
    
    def name_server_loop(self):
        """
        Init the name server.
        """
        init_name_server(self.ns_address[0], self.ns_address[1])
    
    def receiver_server_loop(self):
        """
        Init http receiver server. 
        """
        receiver = HTTPRequestReceiver(self.client_interface_address)
        receiver.start(self)
        
    def get_ring_nodes_availables(self):
        """
        Return a dictionary mapping ring nodes names to its pyro address
        """
        ns = self.get_name_server()
        with ns:
            availables = ns.list(prefix=RingNode.CHORD_NODE_PREFIX)
        return availables
        
    def get_urls(self, urls:List[str])->URLHTMLDict:
        """
        Get the given urls from the system 
        """
        
        availables = self.get_ring_nodes_availables()
        
        if availables:
            node_name, node_address = random.choice([x for x in availables.items()])
            with pyro.Proxy(node_address) as ring:
                return ring.get_urls(urls)
        
        raise DistscrappyError("No Ring Nodes found")
    
