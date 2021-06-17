from typing import List,Dict
import Pyro4 as pyro
import Pyro4.util
from concurrent.futures import ThreadPoolExecutor, Future
from chord.ch_coord import ChordCoordinator
import sys
import logging as log
from chord.ch_shared import *
import time
import random
sys.excepthook = Pyro4.util.excepthook

def operate_id(id1, id2, total_bits, operator):
    """
    Operate id1 and id2 with function operator,  using arithmetic modulo 2**total_bits
    """
    return operator(id1,id2) % (1 << total_bits)

def sum_id(id1, id2, total_bits):
    """
    Sum id1 and id2 using arithmetic modulo 2**total_bits
    """
    return operate_id(id1, id2, total_bits, lambda x,y: x + y)

def sub_id(id1, id2, total_bits):
    """
    Substract id1 and id2 using arithmetic modulo 2**total_bits
    """
    return operate_id(id1, id2, total_bits, lambda x,y: x - y)


class FingerTableEntry:
    
    def __init__(self, node_key:int, entry_bit:int, total_bits:int, successor:int=None):
        self.is_predecessor = entry_bit == 0
        
        if entry_bit == 0: # Predecessor
            entry_bit = 1 # To avoid negative shift

        self.start = sum_id(node_key, 1 << (entry_bit - 1), total_bits)
        self.successor = successor

    def __str__(self):
        return f"{self.start} -> {self.successor}" if not self.is_predecessor else f"Pred -> {self.successor}"

    def __repr__(self):
        return str(self)

@pyro.expose
class ChordNode:
    
    CHORD_NODE_PREFIX = "chord.node."
    
    def hash(self, value):
        """
        Hash function used by ChordNode
        """
        return hash(value) % (self.max_nodes) 
    
    def equal(self, list_value, lookup_value):
        """
        Equal function for comparing values
        """
        return list_value == lookup_value
    
    @classmethod
    def node_name(cls, id):
        """
        Naming convention for ChordNode
        """
        return f"{cls.CHORD_NODE_PREFIX}{id}"

    def _get_successor(self):
        return self.finger_table[1].successor
    
    def _set_successor(self, value):
        self.add_successor_list(value)
        self.finger_table[1].successor = value

    successor = property(_get_successor, _set_successor)

    
    def _get_predecessor(self):
        return self.finger_table[0].successor
    
    def _set_predecessor(self, value):
        self.finger_table[0].successor = value

    predecessor = property(_get_predecessor, _set_predecessor)
    
    def _get_id(self):
        return self._id
    
    def _set_id(self, value):
        """
        Set node id.  
        Id can't change once setted. 
        """
        if self._id == None:
            self._id = value
    
    id = property(_get_id, _set_id)
    
    def __init__(self, host=None, port=0, name_server_host=None, name_server_port=None, forced_id=None, stabilization=True, bits:int=5, ns_addresses=None):
        self.listeners:List[object] = []
        self.host = host
        self.port = port
        self.name_servers = ns_addresses or []
        if name_server_host is not None and name_server_port is not None:
            self.name_servers = list(set(self.name_servers + [(name_server_host,name_server_port)]))
        self._id = None
        self.id = forced_id
        self.bits = bits
        self.max_nodes = 1 << self.bits
        self.max_successor_list_count = self.bits
        self.successor_list:List[object] = []
        self.stabilization = stabilization
        self.running = False
        self.values:Dict[object,object]= {}
        self.executor = ThreadPoolExecutor()

    @method_logger
    def lookup(self, value):
        """
        Returns the value associated with the value 
        """
        key = self.hash(value)
        if self.in_between(key, self.sum_id(self.predecessor, 1), self.sum_id(self.id, 1)):
            equal_hash = self.values[key]
            try:
                return [x for x in equal_hash if self.equal(x, value)][0]
            except IndexError:
                raise KeyError(f"Value {value} not found in DHT")
        successor_id = self.find_successor(key)
        successor = self.get_node_proxy(successor_id)
        return successor.lookup(value)
    
    @method_logger
    def insert(self, value, key=None):
        """
        Insert value into the DHT. If key is given then it will be inserted with it.
        """
        if key != None:
            key = self.hash(key)
        else:
            key = self.hash(value)
        successor_id = self.find_successor(key)
        if successor_id == self.id:
            if key in self.values:
                try:
                    self.values[key].remove(value) # Remove old value if exist
                except ValueError:
                    pass
                self.values[key].append(value)
            else:
                self.values[key] = [value]
        else:
            successor = self.get_node_proxy(successor_id)
            successor.insert(value, key)
    
    @method_logger
    def register_listener(self, listener):
        """
        register an object that listen when the nodes keys changed due to relocation.  
        The listeners must have a key_relocated method that receives a list of integer, indicating   
        the keys that were changed.
        """
        self.listeners.append(listener)
    
    @method_logger
    def notify_listeners(self, keys:list):
        """
        Notify listeners that keys were relocated
        """
        for l in self.listeners:
            l.keys_relocated(keys)
    
    
    def cli_loop(self):
        """
        Command Line Interface to talk with ChordNode
        """
        command = None
        help_msg="ft: print finger table\nid: print node id\nkeys: print local key:value\nsl: print successor list\nexit: shutdown chord node"
        while True:
            command = input()
            if command == "ft":
                print(self.finger_table)
            elif command == "id":
                print(self.id)
            elif command == "keys":
                print("\n".join([f"- {x}:{self.values[x]}" for x in self.values]))
            elif command == "sl":
                print(self.successor_list)
            elif command == "exit":
                self.leave()
                break
            else:
                print("Invalid command:\n", help_msg)
    
    @method_logger
    def leave(self):
        """
        Leave DHT table
        """
        try:
            # Update predecessor and successor and transfer the current keys
            successor_node = self.get_node_proxy(self.successor)
            predecessor_node = self.get_node_proxy(self.predecessor)
            successor_node.predecessor = self.predecessor
            predecessor_node.successor = self.successor
            successor_node.update_values(self.values)
            if not self.stabilization:
                successor_node.update_leaving_node(self.id, successor_node.id)
            else:
                # Stabilization works for itself
                pass
        except Exception as exc:
            log.exception(exc)
        
        try:
            # coordinator = create_object_proxy(self.coordinator_address, self.name_servers)
            # coordinator.unregister(self.id)
            pass
        except Exception as exc:
            log.exception(exc)
            
        self.daemon.shutdown()
    
    def update_leaving_node(self, node_id, new_successor_id):
        """
        Update finger table having node_id with successor_id
        """
        for i in range(1, self.bits + 1):
            finger_table_entry = self.finger_table[i]
            if finger_table_entry.successor == node_id:
                finger_table_entry.successor = new_successor_id
            elif self.in_between(finger_table_entry.successor, self.id, node_id):
                successor_id = self.find_successor(finger_table_entry.successor)
                successor_node = self.get_node_proxy(successor_id)
                successor_node.update_leaving_node(node_id, new_successor_id)
    
    @method_logger
    def update_values(self, new_values:dict):
        """
        Update the values dictionary with new_values
        """
        for x in new_values:
            if self.in_between(x, self.sum_id(self.predecessor, 1), self.sum_id(self.id, 1)):
                self.values[x] = new_values[x]
        
    @method_logger
    def start(self):
        """
        Start the node taking initial_node as reference to fill the finger_table. 
        In case initial_node is None the the current node is the first in the DHT. 
        """
        self.running = True
        
        self.executor.submit(self.cli_loop)
        
        with pyro.Daemon(self.host, self.port) as daemon:
            self.daemon = daemon
            
            initial_node = self.initial_node()
            
            # Register node in pyro name server and deamon
            self.dir = daemon.register(self)
            with locate_ns(self.name_servers) as ns:
                current_prefix = type(self).CHORD_NODE_PREFIX
                nodes = ns.list(prefix=current_prefix)
                
                id = self.hash(self.dir)
                name = type(self).node_name(id)
                try_amount = self.bits
                
                while try_amount > 0:
                    if name not in nodes:
                        self.id = id
                        ns.register(name, self.dir)
                        break
                    import string
                    random_string = "".join(random.choices(string.ascii_uppercase) for _ in range(20))
                    id = self.hash(random_string)
                    name = type(self).node_name(id)
                    try_amount -= 1 
                else:
                    raise ValueError("Can't add node to DHT table, is over populated")
                
            
            # Joining DHT
            self.join(initial_node)

            daemon.requestLoop()
            self.daemon = None
        
        self.running = False
    
    @method_logger
    def initial_node(self):
        """
        Returns an initial Chord node, None if empty 
        """
        with locate_ns(self.name_servers) as ns:
            availables = ns.list(prefix=type(self).CHORD_NODE_PREFIX)
        while availables:
            node_name, node_address = random.choice([x for x in availables.items()])
            try:
                node = create_object_proxy(node_name, self.name_servers)
                node_id = node.id # Check if node is alive
                log.info(f"Returned initial node {node_id} with address {node_address}")
                return node
            except pyro.errors.CommunicationError:
                log.info(f"Node {node_name} offline")
                availables.__delitem__(node_name)
        return None
                
    def in_between(self, key, lwb, upb, equals=True):
        """
        Checks if key is between lwb and upb with modulus 2**bits
        """
        if lwb == upb:
            return equals
        elif lwb < upb:                   
            return lwb <= key and key < upb
        else:                             
            return (lwb <= key and key < upb + self.max_nodes) or (lwb <= key + self.max_nodes and key < upb)                    
   
    @method_logger
    def find_successor(self, key):
        """
        Finds and returns the node's id for key successor
        """
        pred_id = self.find_predecessor(key)
        pred_node = self.get_node_proxy(pred_id)
        return pred_node.successor
    
    @method_logger
    def find_predecessor(self, key):
        """
        Finds and returns the node's id for key predecessor
        """
        current = self
        
        while not (self.in_between(key, self.sum_id(current.id, 1), self.sum_id(current.successor, 1))):
            current_id = current.closest_preceding_finger(key)
            current = self.get_node_proxy(current_id)
            log.debug(f"find_predecessor cycle: key:{key} current_id:{current.id}, current_successor:{current.successor}")
        return current.id
    
    def closest_preceding_finger(self, key):
        """
        Return the closest preceding finger node's id from key
        """
        for i in range(self.bits,0,-1):
            if self.finger_table[i].successor != None and self.in_between(self.finger_table[i].successor, self.sum_id(self.id, 1), key):
                return self.finger_table[i].successor
        return self.id
    
    @method_logger
    def register(self):
        """
        Called when joining the DHT
        """
        # coordinator = create_object_proxy(ChordCoordinator.ADDRESS, self.name_servers)
        # coordinator.register(self.id, self.dir)
        pass
            
    @method_logger
    def join(self, initial_node):
        """
        Do the initialization of the node using initial_node. 
        If initial_node is None then the current node is the first in the DHT 
        """

        self.register()
        
        if initial_node is None:
            # All finger_table entries are self
            self.finger_table = [FingerTableEntry(self.id, i, self.bits, self.id) for i in range(self.bits+1)]
        else:
            # All finger_table entries are None
            self.finger_table = [FingerTableEntry(self.id, i, self.bits, None) for i in range(self.bits+1)]
            
        if not self.stabilization and initial_node != None:
            # Full finger table initialization, doesn't do stabilization
            self.init_finger_table(initial_node)
            self.executor.submit(self.init_node_last_part) # Let the current node accept RPC from now on
        elif self.stabilization:
            # More loose table initialization complemented with periodic calls to maintain the table
            if initial_node != None:
                self.successor = initial_node.find_successor(self.id)
            self.executor.submit(self.stabilize_loop)
            self.executor.submit(self.fix_fingers_loop)
    
    @method_logger
    def stabilize_loop(self):
        """
        Periodically calls stabilize method
        """
        interval_milliseconds = 2000
        while self.running:
            try:
                self.stabilize()
            except Exception as exc:
                log.exception(exc)
            time.sleep(interval_milliseconds/1000)
    
    @method_logger
    def stabilize(self):
        """
        Verifies current node's immediate successor and notifies it about current node's existence
        """
        try:
            old_successor_id = self.find_successor(self.successor)
            old_successor_node = self.get_node_proxy(old_successor_id)
            pred_old_successor_id = old_successor_node.predecessor
            if pred_old_successor_id != None and self.in_between(pred_old_successor_id, self.sum_id(self.id, 1), self.successor, equals=False):
                self.successor = pred_old_successor_id
        except pyro.errors.CommunicationError as exc:
            log.error(f"{exc}")
            new_successor = self.search_posible_successor()
            self.successor = new_successor.id
            old_successor_node = new_successor
        old_successor_node.notify(self.id)
        self.transfer_keys()
        
        
    @method_logger
    def notify(self, node_id):
        """
        Verifies if node_id is a better predecessor, if it is then the predecessor is updated. 
        """
        if self.predecessor != None:
            try:
                predecessor_node = self.get_node_proxy(self.predecessor)
                predecessor_node.id
            except pyro.errors.CommunicationError as e:
                log.info(f"Predecessor {self.predecessor} offline")
                self.predecessor = None

        if self.predecessor == None or self.in_between(node_id, self.sum_id(self.predecessor, 1), self.id):
            self.predecessor = node_id
            predecessor_node = self.get_node_proxy(node_id)
            predecessor_node.transfer_keys()
    
    @method_logger
    def fix_fingers_loop(self):
        """
        Periodically calls fix_fingers method
        """
        interval_milliseconds = 2000
        while self.running:
            try:
                self.fix_fingers()
            except Exception as exc:
                log.exception(exc)
            time.sleep(interval_milliseconds/1000)
    
    @method_logger
    def fix_fingers(self):
        """
        Randomly updates a finger table's entry
        """
        if self.bits < 2:
            return
        update_index = random.randint(2, self.bits)
        finger_table_entry = self.finger_table[update_index]
        finger_table_entry.successor = self.find_successor(finger_table_entry.start)
    
    @method_logger
    def init_finger_table(self, initial_node):
        """
        Fill the node's finger_table using initial_node.
        """
        self.finger_table = [FingerTableEntry(self.id, i, self.bits, None) for i in range(self.bits+1)]
        
        self.successor = initial_node.find_successor(self.finger_table[1].start)
        successor_node = self.get_node_proxy(self.successor)
        # Update predecessors
        self.predecessor = successor_node.predecessor
        successor_node.predecessor = self.id
        # Update finger table
        for i in range(1, self.bits):
            upper_entry = self.finger_table[i+1]
            current_entry = self.finger_table[i]
            if self.in_between(upper_entry.start, self.id, current_entry.successor):
                upper_entry.successor = current_entry.successor
            else:
                without_this_node_succ = initial_node.find_successor(upper_entry.start)
                if self.in_between(self.id, upper_entry.start, without_this_node_succ, equals=False):
                    upper_entry.successor = self.id
                else:
                    upper_entry.successor = without_this_node_succ
    
    @method_logger
    def init_node_last_part(self):
        """
        Update others finger table nodes with current node.    
        Transfer the associated keys into this node.  
        """
        self.update_others()
        self.transfer_keys()
    
    @method_logger
    def update_others(self):
        """
        Update finger tables of nodes that should include this node
        """
        for i in range(1, self.bits + 1):
            # In the paper the +1 at the of 2**(i-1) doesn't exist but try example CHORD 3 then CHORD 5 and the FT of 3 doesn't update properly
            pred_id = self.find_predecessor(self.sub_id(self.id, (2 ** (i-1)) - 1))
            pred_node = self.get_node_proxy(pred_id)
            pred_node.update_finger_table(self.id, i)
            
    @method_logger
    def transfer_keys(self):
        """
        Brings the successor key values for what this node is responsible.
        """
        successor_id = self.find_successor(self.successor)
        successor_node = self.get_node_proxy(successor_id)
        new_keys = successor_node.pop_keys(self.sum_id(self.predecessor, 1), self.id)
        self.values.update(new_keys)
    
    @method_logger
    def pop_keys(self, lower_bound:int, upper_bound:int):
        """
        Remove associated values within lower_bound and upper_bound. Both limits included
        
        Return the removed part of the dictionary.
        """
        keys = [x for x in self.values if self.in_between(x, lower_bound, self.sum_id(upper_bound, 1))]
        values = [self.values[x] for x in keys]
        for k in keys:
            self.values.__delitem__(k)
        
        if keys:
            self.executor.submit(self.notify_listeners, keys)
        
        return {k:v for k,v in zip(keys, values)}
                
    @method_logger
    def update_finger_table(self, s:int, i:int):
        """
        Updates figer table at i if s is better suited
        """
        if self.id == s:
            return
        
        if self.in_between(s, self.id, self.finger_table[i].successor):
            self.finger_table[i].successor = s
            pred_node = self.get_node_proxy(self.predecessor)
            pred_node.update_finger_table(s, i)
                
    def get_node_proxy(self, id:int):
        """
        Returns a Chord Node proxy for the given id
        """
        if id != self.id:
            node = create_object_proxy(ChordNode.node_name(id), self.name_servers)
        else:
            node = self
        return node
    
    def add_successor_list(self, successor_id):
        """
        Add successor_id to successor list
        """
        self.successor_list.append(successor_id)
        self.successor_list = list(set(self.successor_list))
        self.successor_list.sort(key=lambda x: x+(self.max_nodes) if x < self.id else x)
        self.successor_list = self.successor_list[:self.max_successor_list_count]
    
    def sum_id(self, id1, id2):
        """
        Sum id1 and id2 with arithmetic modulo 2**bits
        """
        return sum_id(id1, id2, self.bits)
    
    def sub_id(self, id1, id2):
        """
        Substract id1 and id2 with arithmetic modulo 2**bits
        """
        return sub_id(id1, id2, self.bits)
    
    def search_posible_successor(self):
        """
        Returns a possible new active successor.   
        It looks to the successor_list and finger table entries.  
        If any are active the only active si self. 
        """
        
        def return_node(node_id):
            try:
                node = self.get_node_proxy(node_id)
                testing_proxy = node.id
                return node
            except pyro.errors.CommunicationError as exc:
                log.error(f"Node {node_id} offline.")
                try:
                    self.successor_list.remove(node_id)
                except ValueError:
                    pass
        
        nodes_ids = self.successor_list.copy()
        for node_id in nodes_ids: # Trying with successor list
            node = return_node(node_id)
            if node:
                return node
        
        for i in range(2, self.bits + 1): # Trying with finger table
            finger_able_entry = self.finger_table[i]
            successor_id = finger_able_entry.successor
            if successor_id != None:
                node = return_node(successor_id)
                if node:
                    return node
        
        # raise ValueError(f"No available successor node") 
        return self.id
                    
                    