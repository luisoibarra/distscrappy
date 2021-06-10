from node.base import Node
from typing import List,Dict,Tuple

class ScrapperNode(Node):
    """
    Node in charge of fetch the urls from the network
    """
    
    def start(self):
        pass # Main Node Method
    
    def fetch_urls(self, urls:List[str])->Dict[str,str]:
        """
        Fetch all urls form the list returning a dictionary mapping each url to its html
        """
        pass