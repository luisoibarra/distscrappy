from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from shared.clock import ClockMixin
from shared.utils import wait
from chord.ch_node import ChordNode, sum_id
from chord.ch_shared import create_object_proxy, locate_ns, method_logger
from typing import List,Dict,Tuple, Union
from shared.const import *
from config import CACHE_THRESHOLD_SECONDS, WRITE_AMOUNT_SAVE_STATE
from server.storage import StorageNode
from shared.logger import LoggerMixin
from server.fetcher import URLFetcher
from shared.error import ScrapperError
from Pyro4 import URI
import Pyro4 as pyro
import time
from threading import Barrier
import hashlib

@pyro.expose
class RingNode(LoggerMixin,ClockMixin, ChordNode):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetcher = URLFetcher()
        self.writes_amount = 0
    
    def is_responsible_for(self, id:int)->bool:
        """
        Returns if current node is responsable for saving given id
        """
        return self.in_between(id, self.predecessor+1, self.id+1)
    
    def hash(self, value:URLState):
        """
        Overriden hash function to provide DictionarySupport
        """
        if isinstance(value, (URI, str, int)):
            return self.url_hash(value)
        return self.url_hash(value[ST_URL])
    
    def equal(self, list_value:URLState, lookup_value:str):
        """
        Overriden equal function for comparing values
        """
        return list_value[0] == lookup_value

    def entry_equal(self, entry1:URLState, entry2:URLState):
        return entry1[ST_URL] == entry2[ST_URL] 

    def url_hash(self, url:Union[URI, str, int]):
        """
        Hash function used to get urls hash
        """
        h = hashlib.sha256()
        h.update(str(url).encode())
        return int(h.hexdigest(), 16) % self.max_nodes
    
    def get_urls(self, urls:List[str])->URLHTMLDict:
        """
        Get a given urls list
        """
        url_html_dict: URLHTMLDict = {}
        
        # for url in urls: # TODO Maybe some threads can be created here
        
        # Start the load operations and mark each future with its URL
        fetch_tasks = [self.executor.submit(self.process_get_url, url) for url in urls]

        for task in as_completed(fetch_tasks):
            self.log_info("Download Task done")
            try:
                result = task.result()
                self.log_info(f"Downloaded at {self.id}: {result[0]}")
                url_html_dict[result[0]] = result[1]
            except Exception as e:
                self.log_error(f"Downloading error at {self.id}: {e}")
        
        for url in urls:
            if not url in url_html_dict:
                url_html_dict[url] = get_scrapped_info(None, "Problem scrapping url")
            
        return url_html_dict

    def process_get_url(self, url:str)-> Tuple[str,SCRAPPED_INFO]:
        
        state = self.fetch_url_state(url)
        self.log_debug(f"URL State DHT: {str(state)[:200]}")
        # Exist entry in DHT
        if state is not None and self.is_cache_valid(state):
            self.log_info(f"Cache Hit for {url}")
            return url, get_scrapped_info(state[ST_HTML], None)
        else:
            self.log_info(f"Downloading {url}")
            try:
                fetched_state = self.fetch_url(url, True)
                self.insert_state(fetched_state)
                return url, get_scrapped_info(fetched_state[ST_HTML], None)
            except Exception as exc:
                return url, get_scrapped_info(None, str(exc))
    
    def create_other_tasks(self):
        super().create_other_tasks()
        self.load_entries()
    
    @method_logger
    def insert_state(self, state:URLState):
        """
        Insert given state into the DHT
        """
        state_hash = self.hash(state)
        succ = self.find_successor(state_hash)
        succ_node = self.get_node_proxy(succ)
        succ_node.insert(state)
        self.writes_amount += 1
        if self.writes_amount >= WRITE_AMOUNT_SAVE_STATE:
            self.save_entries()
    
    @method_logger
    def fetch_url(self, url:str, state_checked:bool=False)->URLState:
        """
        Create and return a URLState for given url. If state_checked it will not verify if the 
        url is already in the DHT 
        """
        url_hash = self.url_hash(url)
        if self.is_responsible_for(url_hash): 
            # Current node must perform the fetching process
            
            if not state_checked: # Check if already in DHT
                state = self.fetch_url_state(url)
                if state is not None and self.is_cache_valid(state):
                    return state

            #  Fetch URL
            scrapped = self.fetcher.fetch_url(url)
            if scrapped[SCR_ERROR]:
                print(scrapped[SCR_ERROR], type(scrapped[SCR_ERROR]))
                raise Exception(scrapped[SCR_ERROR])
            else:
                return get_url_state(url, self.get_ds_time(), scrapped[SCR_HTML])
        else:
            # Other node is responsible for this url
            suc = self.find_successor(url_hash)
            node = self.get_node_proxy(suc)
            return node.fetch_url(url)
    
    @method_logger
    def save_entries(self):
        """
        Save node entries
        """
        try:
            storage = self.get_storage_node()
            storage.save_entries(self.values)
            self.log_info(f"Node entries saved")
            self.writes_amount = 0 # Reset write
        except Exception as exc:
            self.log_exception(exc)
    
    
    def get_entries_to_load(self):
        """
        Get the entries between predecessor + 1 and id
        """
        # Getting current node ids
        entries = []
        lwb = i = sum_id(self.predecessor, 1, self.bits)
        upb = sum_id(self.id, 1, self.bits)
        first = True
        while self.in_between(i, lwb, upb, first) and len(entries) < 300:
            entries.append(i)
            i = sum_id(i, 1, self.bits)
            first = i != upb
        return entries
            
    @method_logger
    def load_entries(self):
        """
        Load node entries
        """
        while self.running: # Active until the storage node is found
            try:
                entries = self.get_entries_to_load()
                self.log_info(f"Loading node entries {entries}")
                storage = self.get_storage_node()
                save_entries = storage.get_entries(entries)
                self.update_state_values(save_entries)
                self.log_info(f"Info loaded from storage")
                break
            except Exception as exc:
                self.log_error(str(exc))
            time.sleep(40)
    
    def get_storage_node(self)-> StorageNode:
        """
        Returns an object proxy of the storage node
        """
        attempt = 2
        exc = None
        while attempt > 0:
            try:
                storage = create_object_proxy(StorageNode.NAME_PREFIX, self.name_servers)
                return storage
            except Exception as ex:
                exc = ex
                attempt -= 1
                time.sleep(1)
        raise exc
    
    def leave(self):
        self.save_entries()
        return super().leave()
    
    def update_state_values(self, new_states: Dict[int,List[URLState]]):
        """
        Update values with given values taking in count posible conflicts.
        """
        values = {}
        for i in new_states:
            current_entries = self.values.get(i, [])
            for entry in new_states[i]:
                try:
                    saved = next(x for x in current_entries if x[ST_URL] == entry[ST_URL])
                    if saved[ST_FETCH_TIME] < entry[ST_FETCH_TIME]:
                        current_entries.remove(saved)
                        current_entries.append(entry)
                except StopIteration:
                    current_entries.append(entry)
            values[i] = current_entries
        self.update_values(values)
                
    def is_cache_valid(self, state:URLState):
        """
        Return if the HTML is valid to return to the client 
        """
        # TODO Something more fancy?
        fetch_time = state[ST_FETCH_TIME]
        diff = abs(self.get_ds_time() - fetch_time)
        if fetch_time != None and diff < CACHE_THRESHOLD_SECONDS:
            return True
        return False
        
    def get_ds_time(self)->float:
        """
        Returns the distributed time stamp
        """
        return self.getClockTime()
    
    def fetch_url_state(self, url:str)->URLState:
        try:
            state = self.lookup(url)
            return state
        except KeyError: # Not found => Not currently active 
            return None
