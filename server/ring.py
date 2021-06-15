from shared.clock import ClockMixin
from chord.ch_node import ChordNode
from chord.ch_shared import create_object_proxy, method_logger
from typing import List,Dict,Tuple
from shared.const import *
from shared.logger import LoggerMixin
from server.fetcher import URLFetcher
from shared.error import ScrapperError
from Pyro4 import URI
import Pyro4 as pyro
import time

@pyro.expose
class RingNode(LoggerMixin,ClockMixin, ChordNode):
    
    CACHE_THRESHOLD_SECONDS = 60
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetcher = URLFetcher()
    
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

    def url_hash(self, url:str):
        """
        Hash function used to get urls hash
        """
        return super().hash(url)
    
    def get_urls(self, urls:List[str])->URLHTMLDict:
        """
        Get a given urls list
        """
        url_html_dict = {}
        
        for url in urls: # TODO Maybe some threads can be created here
            state = self.fetch_url_state(url)
            if state is not None and self.is_cache_valid(state): # Exist entry in DHT
                self.log_info(f"Cache Hit for {url}")
                url_html_dict[url] = get_scrapped_info(state[ST_HTML], None)
            else:
                self.log_info(f"Downloading {url}")
                try:
                    fetched_state = self.fetch_url(url, True)
                    self.insert_state(fetched_state)
                    url_html_dict[url] = get_scrapped_info(fetched_state[ST_HTML], None)
                except Exception as exc:
                    url_html_dict[url] = get_scrapped_info(None, exc.args[0])

        return url_html_dict
    
    @method_logger
    def insert_state(self, state:URLState):
        """
        Insert given state into the DHT
        """
        state_hash = self.hash(state)
        succ = self.find_successor(state_hash)
        succ_node = self.get_node_proxy(succ)
        succ_node.insert(state)
    
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
                raise ScrapperError(scrapped[SCR_ERROR])
            else:
                return get_url_state(url, self.get_ds_time(), scrapped[SCR_HTML])
        else:
            # Other node is responsible for this url
            suc = self.find_successor(url_hash)
            node = self.get_node_proxy(suc)
            return node.fetch_url(url)
    
    def is_cache_valid(self, state:URLState):
        """
        Return if the HTML is valid to return to the client 
        """
        # TODO Something more fancy?
        fetch_time = state[ST_FETCH_TIME]
        if fetch_time != None and self.get_ds_time() - fetch_time > CACHE_THRESHOLD_SECONDS: # One minute cache threshold. Only temporary
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
