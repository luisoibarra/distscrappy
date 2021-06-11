from node.base import Node
from typing import List,Dict,Tuple
import urllib.request as urequest, urllib.parse as uparse
from urllib.error import URLError

class ScrapperNode(Node):
    """
    Node in charge of fetch the urls from the network
    """

    def start(self):
        pass # Main Node Method
    
    def fetch_urls(self, urls:List[str])-> Dict[str,str]:
        """
        Fetch all urls from the list returning a dictionary mapping each url to its html
        """
        d =  Dict()

        for url in urls:
            try:
                if self._url_validator(url):
                    response = urequest.urlopen(url)
                    webContent = response.read()
                    d[url] = webContent
            except URLError as e:
                d[url] = e
        
        return d

    def _url_validator(self,url:str)-> url:str:
            o = uparse.urlparse(url)
            if o.scheme not in ["https","http","ftp","ftps"]:
                o.scheme = "https"
                url = o.geturl()
            return all([o.scheme,o.netloc,o.path])
