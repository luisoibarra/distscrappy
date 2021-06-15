import urllib.request as urequest, urllib.parse as uparse
from urllib.error import URLError
from shared.const import *
from concurrent.futures import ThreadPoolExecutor, Future
from shared.logger import LoggerMixin
import time

class URLFetcher(LoggerMixin):
    """
    Sync-Async URL Fetcher  
    Returns URLs in a sync way but are downloaded in an async way.
    """
    
    def __init__(self):
        self.executor = ThreadPoolExecutor()
        self.downloading = {} # Mapps URL to Future    
    
    def fetch_url(self, url:str)->SCRAPPED_INFO:
        """
        Fetch given url    
        """
        # TODO More robust fetcher?
        
        try:
            self.log_info(f"Request {url}")
            if url in self.downloading:
                self.log_debug(f"Requested {url} already downloading")
                task = self.downloading[url]
                return  get_scrapped_info(task.result(), None)
            else:
                def download():
                    """
                    Download url function
                    """
                    if self._url_validator(url):
                        response = urequest.urlopen(url)
                        webContent = response.read()
                        return webContent.decode()
                    raise URLError("Invalid url")
                
                def finish_downloading_callback(task:Future):
                    """
                    Finish download callback. 
                    Remove the task from the downloading dictionary
                    """
                    time.sleep(5) # Wait some time before delete the result
                    self.downloading.__delitem__(url) # Remove url from downloading dictionary
                
                task = self.executor.submit(download)
                self.downloading[url] = task
                task.add_done_callback(finish_downloading_callback)
                return get_scrapped_info(task.result(), None)
        except Exception as ex:
            exc = str(ex.args[0])
            self.log_exception(ex)
            return get_scrapped_info(None, exc)

    def _url_validator(self,url:str)->bool:
        """
        Check if url is valid
        """
        o = uparse.urlparse(url)
        if o.scheme not in ["https","http","ftp","ftps"]:
            o.scheme = "https"
            url = o.geturl()
        return all([o.scheme,o.netloc,o.path]) or all([o.scheme, o.netloc])
    