from Pyro4.core import URI
from config import STORAGE_NS_SYNC_DELAY_SECONDS
from shared.logger import LoggerMixin
from shared.const import *
import Pyro4 as pyro
from Pyro4.errors import PyroError
from chord.ch_shared import locate_ns, create_object_proxy
from shared.error import StorageError
import time
from typing  import List, Dict
import json
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Lock


@pyro.expose
class StorageNode(LoggerMixin):
    """
    Handles Storage
    """
    
    DATA_BASE_PATH = "data"
    
    FILE_PREFIX = "node_entries"
    
    NAME_PREFIX = "storage"
    
    def __init__(self, ns_dirs: List[IP_DIR], node_dir: IP_DIR) -> None:
        self.rw_mutex: Dict[int,Lock] = {} # Mutex for read-write operation on given node 
        self.dict_mutex = Lock() # For keeping re_mutex dictionary consistent
        self.acquire_mutex = Lock() # Avoid posible dead lock when requesting same nodes at the same time  
        base = type(self).DATA_BASE_PATH
        self.ns_dirs = ns_dirs
        self.node_dir = node_dir
        if not os.path.isdir(base):
            os.mkdir(base)
        self.running = False
        self._dir = None
        
    def _get_lock(self, id:int)->Lock:
        """
        Returns the lock object for given id
        """
        with self.dict_mutex:
            lock = self.rw_mutex.get(id,None)
            if lock is None:
                lock = Lock()
                self.rw_mutex[id] = lock
            return lock
    
    def _acquire_multiple(self, ids: List[int]):
        """
        Acquire at the same time multiple id locks
        """
        with self.acquire_mutex:
            self.log_debug(f"Acquiring {ids}")
            locks = [self._get_lock(id) for id in ids]
            for l in locks:
                l.acquire()
    
    def _release_multiple(self, ids: List[int]):
        """
        Release at the same time multiple id lock
        """
        with self.acquire_mutex:
            self.log_debug(f"Releasing {ids}")
            locks = [self._get_lock(id) for id in ids]
            for l in locks:
                l.release()
    
    @property
    def dir(self):
        return self._dir
    
    def start(self):
        """
        Starts storage node service
        """
        
        self.running = True
        with pyro.Daemon(self.node_dir[0], self.node_dir[1]) as daemon:
            self._dir = daemon.register(self)
            executor = ThreadPoolExecutor()
            executor.submit(self.register_ns_loop, self._dir)
            self.log_info("Storage Node Started")
            daemon.requestLoop(lambda : self.running)
        executor.shutdown()
    
    def stop(self):
        """
        Stops storage node service
        """
        self.running = False
        
    def register_ns_loop(self, dir:URI):
        """
        Periodiacally register in the name servers
        """
        while self.running:
            try:
                try:
                    storage = create_object_proxy(type(self).NAME_PREFIX, self.ns_dirs)
                    storage_dir = str(storage.dir)
                    self_dir = str(self.dir)
                    if storage_dir > self_dir:
                        self.log_error("A storage node is already available")
                        self.stop()
                        break
                    elif storage_dir < self_dir:
                        self.log_debug("Stopping in use storage node")
                        storage.stop()
                        self.log_debug("Storage node stopped")
                        time.sleep(5)
                except PyroError as perr:
                    self.log_info("Registering storage node")
                    
                with locate_ns(self.ns_dirs) as ns:
                    ns.register(type(self).NAME_PREFIX, dir)
                    
            except Exception as exc:
                self.log_exception(exc)
            time.sleep(STORAGE_NS_SYNC_DELAY_SECONDS)
    
    def save_entries(self, entries_dict: Dict[int, List[URLState]]):
        """
        Save the entries into the database
        """
        self.log_info(f"Saving entries {list(entries_dict.keys())}")
        
        self._acquire_multiple(list(entries_dict.keys()))
        prev_values: Dict[int, List[URLState]] = {}
        
        for id, entries in entries_dict.items():
            try:
                # Saving previous entries in case of failure
                entry = self._load_entry_json(id)
                prev_values[id] = entry
                
                self._save_entry_json(id, entries)
                self.log_debug(f"Entries for id {id} saved")
            except Exception as exc:
                self.log_error(f"Entry {id} save error: {exc}")
                # Restore values to previous state
                for id, entries in prev_values.items():
                    self._save_entry_json(id, entries)
                self._release_multiple(list(entries_dict.keys()))
                raise StorageError(str(exc))
        self._release_multiple(list(entries_dict.keys()))
    
    def get_entries(self, ids: List[int])-> Dict[int, List[URLState]]:
        """
        Returns the entries for given ids
        """
        self.log_info(f"Getting entries for {ids}")
        
        self._acquire_multiple(ids)
        entries: Dict[int, List[URLState]] = {}
        
        for id in ids:
            try:
                id_entries = self._load_entry_json(id)
                if id_entries:
                    entries[id] = id_entries
                self.log_debug(f"Entry for {id} fetched")
            except Exception as exc:
                self.log_error(f"Entry {id} error: {exc}")
                self._release_multiple(ids)
                raise StorageError(str(exc))
        
        self._release_multiple(ids)
        return entries
    
    def _get_json_path(self, id):
        """
        Returns the name for the json file associated with given id
        """
        return os.path.join(type(self).DATA_BASE_PATH, f"{type(self).FILE_PREFIX}{id}.json")
    
    def _save_entry_json(self, id: int, entries: List[URLState]):
        """
        Saves the entries into a json file
        """
        with open(self._get_json_path(id), mode='w') as file:
            json.dump(entries, file)
    
    def _init_json_file(self, id: int):
        """
        Creates the initial json file with an empty list if doesn't exist
        """
        filename = self._get_json_path(id)
        try:
            with open(filename, mode="x") as file:
                json.dump([],file)
        except FileExistsError:
            pass
        
    def _load_entry_json(self, id: int)-> List[URLState]:
        """
        Returns the data entries associated with given id
        """
        if not os.path.exists(self._get_json_path(id)):
            return []
        
        self._init_json_file(id)
        
        filename = self._get_json_path(id)
        with open(filename) as file:
            return json.load(file)
        
    