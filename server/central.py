from server.name_server_sync import NSSync
from server.coordinator import Coordinator
from server.timing import TimeSynchronization
from shared.logger import LoggerMixin
from shared.const import *
import Pyro4 as pyro
from concurrent.futures import ThreadPoolExecutor, Future, CancelledError
from chord.ch_ns import init_name_server 
from server.ring import RingNode
from server.receiver import HTTPRequestReceiver
from chord.ch_shared import create_object_proxy, locate_ns
import random
from shared.error import DistscrappyError
import time
from typing  import List, Tuple

class CentralNode(LoggerMixin):
    """
    Central node that supports the name server and acts as client interface
    """
    
    def __init__(self, ns_address:IP_DIR, client_interface_address:IP_DIR, zmq_address:IP_DIR, server_addresses: List[ServerInfo]):
        self.client_interface_address = client_interface_address
        self.ns_address = ns_address
        self.server_addresses = server_addresses
        self.zmq_address = zmq_address
        self.executor = ThreadPoolExecutor()
        self.coordinator = Coordinator(self.zmq_address, [z for _,_,z in self.server_addresses])
        self.ns_sync = NSSync([ns_address] + [x[SERV_NS] for x in server_addresses])
        self.receivers_tasks = None
        self.name_server_tasks = None
        self.running = False
        self.ns_daemon = None
    
    def start(self):
        """
        Start central node
        """
        self.running = True
        
        self.name_server_tasks = []
        self.receivers_tasks = []

        ns_task = self.executor.submit(self.name_server_loop)
        self.name_server_tasks.append(ns_task)

        rec_task = self.executor.submit(self.receiver_server_loop)
        self.receivers_tasks.append(rec_task)
        
        cli_task = self.executor.submit(self.cli_loop)
        
        time.sleep(1)

        for ns_task in self.name_server_tasks:
            ns_task.add_done_callback(self._task_finish_callback("Name server"))
        for rec_task in self.receivers_tasks:
            rec_task.add_done_callback(self._task_finish_callback("Receiver"))
        
        self.coordinator_task = self.executor.submit(self.coordinator.start)

        ts = TimeSynchronization()
        time_task = None
        
        sync_ns_task = None
        
        while self.running:
            time.sleep(1)
            if self.coordinator.is_coordinator: # Coordinator checks
                if time_task is None or not time_task.running():
                    # Start time sync task
                    ns_adresses = [self.ns_address] + [x[SERV_NS] for x in self.server_addresses]
                    time_task = self.executor.submit(ts.startConnecting, ns_adresses)
                if sync_ns_task is None or not sync_ns_task.running():
                    # Start name server update task
                    sync_ns_task = self.executor.submit(self.ns_sync.start)
            else: # Non coordinator checks
                if time_task is not None and time_task.running():
                    ts.stop()
                    time_task.result()
                if sync_ns_task is not None and sync_ns_task.running():
                    self.ns_sync.stop()
                    sync_ns_task.result()

        self.log_info("Central Node Finished")

    def stop(self):
        """
        Stops the node
        """
        self.running = False
        self.log_info("Stopping Central Node")
        self.log_debug("Stopping name server")
        if self.ns_daemon:
            self.ns_daemon.shutdown()
        self.log_debug("Cancelling tasks")
        for task in self.name_server_tasks + self.receivers_tasks:
            task.cancel()
        self.log_debug("Executor is shutdown")
        self.coordinator.stop()
        self.log_debug("Shutting down executor")
        self.executor.shutdown()


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
        return locate_ns([self.ns_address] + [x[SERV_NS] for x in self.server_addresses])
    
    def name_server_loop(self):
        """
        Init the name server.
        """
        while self.running:
            try:
                self.log_info(f"Name server started at {self.ns_address}")
                self.ns_daemon = init_name_server(self.ns_address[0], self.ns_address[1], True)
                self.ns_daemon.requestLoop()
            except Exception as exc:
                if self.ns_daemon:
                    self.ns_daemon.shutdown()
                restart = 5
                self.log_error(f"Name server stopped, restarting in {restart} seconds")
                self.log_exception(exc)
                time.sleep(restart)
                
    def receiver_server_loop(self):
        """
        Init http receiver server. 
        """
        receiver = HTTPRequestReceiver(self.client_interface_address)
        while self.running:
            try:
                self.log_info(f"Receiver started at {self.client_interface_address}")
                receiver.start(self)
            except Exception as exc:
                self.log_error(f"Receiver stopped, restarting in {restart} seconds")
                receiver.stop()
                restart = 5
                self.log_exception(exc)
                time.sleep(restart)

    def cli_loop(self):
        """
        Command line interface.
        """
        help_msg = "Commands:\n\nhelp: prints this message\nstop: Stop current node\n"
        pre_msg = f"Central {self.server_addresses}\n"
        while self.running:
            command = input()
            if not command:
                print(help_msg)
                continue
            command, *args = command.split()
            if command == "help":
                print(help_msg)
            if command == "stop":
                self.stop()
                break
            else:
                print(f"Unrecognized command {command}")
                print(help_msg)

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
    
