from typing import Dict, List
from shared.logger import LoggerMixin
from shared.const import *
from concurrent.futures import ThreadPoolExecutor, Future
import zmq
import random

class Coordinator(LoggerMixin):
    """
    Bullying Coordinator Algorithm
    """
    
    def __init__(self, current_address: IP_DIR, other_addresses: List[IP_DIR], context:zmq.Context = None, executor: ThreadPoolExecutor=None) -> None:
        self.address = current_address
        self.other_addresses = other_addresses
        self.is_coordinator = False
        self.coordinator_dir = None
        self.context = context or zmq.Context()
        self.executor = executor or ThreadPoolExecutor()
        self.running = False

    def is_higher(self, address:IP_DIR)->bool:
        """
        Retuns a number to compare address
        """
        return self.address < address
    
    def reset_coordinator(self):
        """
        Reset Coordinator in order to find a new one
        """
        self.coordinator_dir = None
        self.is_coordinator = False
    
    def start(self):
        """
        Start coordinator routine
        """
        
        higher_addresses = [x for x in self.other_addresses if self.is_higher(x)]

        self.running = True
        sock_rep = self.context.socket(zmq.REP)
        sock_rep.bind(f"tcp://{self.address[0]}:{self.address[1]}")
        
        election_tasks:List[Future] = []
        def finish_callback(task:Future):
            if task in election_tasks:
                election_tasks.remove(task)
            try:
                exc = task.exception(0)
                if exc:
                    raise exc
            except Exception as exc:
                self.log_exception(exc)
                
        timeout_milliseconds = 3000 + random.randint(-1500,1500)
        while self.running:
            value = sock_rep.poll(timeout_milliseconds)
            if value == zmq.POLLIN:
                data = sock_rep.recv_json()
                if data["type"] == "ELECTION":
                    
                    self.log_debug(f"ELECTION Received from {data['sender']}")
                    
                    sock_rep.send_json({
                        "type":"ELECTION_RESPONSE",
                        "sender":self.address,
                        "data":"OK"
                    })
                    task = self.executor.submit(self.do_election_received, higher_addresses)
                    task.add_done_callback(finish_callback)
                    election_tasks.append(task)
                    
                elif data["type"] == "COORDINATOR":
                    self.is_coordinator = False
                    self.coordinator_dir = data["sender"]
                    self.log_info(f"COORDINATOR is {self.coordinator_dir}")
                    sock_rep.send_json({
                        "type":"COORDINATOR_RESPONSE",
                        "sender":self.address,
                        "data":"OK"
                    })
                else:
                    self.log_error(f"Invalid message type {data['type']}")
            elif self.coordinator_dir == None:
                if not self.other_addresses:
                    self.log_info(f"COORDINATOR is {self.address}")
                    self.is_coordinator = True
                    self.coordinator_dir = self.address
                elif random.random() < 1/len(self.other_addresses): # Ideally only one start the coordination procedure
                    if not election_tasks: # Start first election
                        task = self.executor.submit(self.do_election_received, higher_addresses)
                        task.add_done_callback(finish_callback)
                        election_tasks.append(task)
            
    def do_election_received(self, higher_addresses: List[IP_DIR]):
        """
        Send election messages to heigher nodes and in case of been coordinator also send the 
        corresponding messages
        """
        # Send ELECTION to Higher nodes
        election_sended = False
        poll_interval = 10000
        for x in higher_addresses:
            try:
                with self.context.socket(zmq.REQ) as sock_req:
                    self.log_debug(f"Sending ELECTION to {x}")
                    sock_req.connect(f"tcp://{x[0]}:{x[1]}")
                    sock_req.send_json({
                        "type":"ELECTION",
                        "sender":self.address,
                    })
                    action = sock_req.poll(poll_interval)
                    if action == zmq.POLLIN:
                        data = sock_req.recv_json()
                        election_sended = data["data"] == "OK"
                    else:
                        raise TimeoutError(f"Node {x[0]}:{x[1]} not responding after {poll_interval} milliseconds")
            except zmq.error.ZMQError as exc:
                self.log_exception(exc)
            except TimeoutError as exc:
                self.log_exception(exc)
        
        if election_sended:
            self.is_coordinator = False
        else: # Notify all that this node is the coordinator
            self.is_coordinator = True
            self.coordinator_dir = self.address
            for x in self.other_addresses:
                try:
                    with self.context.socket(zmq.REQ) as sock_req:
                        self.log_debug(f"Sending COORDINATOR to {x}")
                        sock_req.connect(f"tcp://{x[0]}:{x[1]}")
                        sock_req.send_json({
                            "type":"COORDINATOR",
                            "sender":self.address,
                        })
                        action = sock_req.poll(poll_interval)
                        if action == zmq.POLLIN:
                            data = sock_req.recv_json()
                        else:
                            raise TimeoutError(f"Node {x[0]}:{x[1]} not responding after {poll_interval} milliseconds")
                except zmq.error.ZMQError as exc:
                    self.log_exception(exc)
                except TimeoutError as exc:
                    self.log_exception(exc)
                    
    def stop(self):
        """
        Stops coordinator routine and clean resources
        """
        self.running = False
        self.context.term()
        self.executor.shutdown()
