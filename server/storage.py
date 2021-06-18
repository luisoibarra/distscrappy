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
from shared.error import StorageError
import time
from typing  import List, Dict
import json
import os

class StorageNode(LoggerMixin):
    """
    Handles Storage
    """
    
    DATA_BASE_PATH = "data"
    
    def save_entries(self, entries: Dict[int, List[URLState]]):
        """
        Save the entries into the database
        """
        self.log_info(f"Saving entries {list(entries.keys())}")
        
        prev_values: Dict[int, List[URLState]] = {}
        
        for id, entries in entries.items():
            try:
                # Saving previous entries in case of failure
                entry = self.load_entry_json(id)
                prev_values[id] = entry
                
                self.save_entry_json(id, entries)
                self.log_debug(f"Entries for id {id} saved")
            except Exception as exc:
                self.log_error(f"Entry {id} save error: {exc}")
                # Restore values to previous state
                for id, entries in prev_values.items():
                    self.save_entry_json(id, entries)
                raise StorageError(str(exc))
    
    def get_entries(self, ids: List[int])-> Dict[int, List[URLState]]:
        """
        Returns the entries for given ids
        """
        self.log_info(f"Getting entries for {ids}")
        
        entries: Dict[int, List[URLState]] = {}
        
        for id in ids:
            try:
                id_entries = self.load_entry_json(id)
                entries[id] = id_entries
                self.log_debug(f"Entry for {id} fetched")
            except Exception as exc:
                self.log_error(f"Entry {id} error: {exc}")
                raise StorageError(str(exc))
        
        return entries
    
    def get_json_path(self, id):
        """
        Returns the name for the json file associated with given id
        """
        return os.path.join(type(self).DATA_BASE_PATH, f"{id}.json")
    
    def save_entry_json(self, id: int, entries: List[URLState]):
        """
        Saves the entries into a json file
        """
        with open(self.get_json_path(id), mode='w') as file:
            json.dump(entries, file)
    
    def init_json_file(self, id: int):
        """
        Creates the initial json file with an empty list if doesn't exist
        """
        filename = self.get_json_path(id)
        try:
            with open(filename, mode="x") as file:
                json.dump([],file)
        except FileExistsError:
            pass
        
    def load_entry_json(self, id: int)-> List[URLState]:
        """
        Returns the data entries associated with given id
        """
        
        self.init_json_file(id)
        
        filename = self.get_json_path(id)
        with open(filename) as file:
            return json.load(file)
        
    