from shared.const import *
import json
import http.client as http_c
import random
from typing import List,Dict
from bs4 import BeautifulSoup


class DistScrappyClient:
    
    def __init__(self, server_dirs:List[IP_DIR]):
        self.server_dirs = server_dirs
        
    def get_urls(self, urls:List[str],deep_level:int):
        """
        Request given urls.
        """
        server_dirs = self.server_dirs.copy()
        errors = []
        levels = {}

        random.shuffle(server_dirs)
        for host, port in server_dirs:
            conn = http_c.HTTPConnection(host, port)
            try:

                actual_deep = 0
                urls_domains = [url[8:] if url[:7].find("http://") != -1 else url for url in urls]
                scrapped_urls = []

                while(actual_deep<=deep_level):
                
                    urls = [url if url[:7].find(
                        "http://") != -1 or url[:8].find("https://") != -1 else'http://' + url for url in urls]
                    urls = [url[:-1] if url[-1:].find('/') != -1 else url for url in urls]

                    scrapped_urls.extend(urls)

                    content = self.build_json_string(urls)
                    conn.request("GET", "urls", content, {"Content-Length":len(content)})
                    resp = conn.getresponse()
                    code = resp.getcode()
                    body = resp.read()
                    if code == 200:

                        json_body = json.loads(body.decode())

                        levels[actual_deep] = json_body

                        actual_deep+=1

                        urls.clear() # Clear the urls list for avoiding innecessary scrapping
                                    # Dont worry... urls are saved in urls_domains for each level that is completed
                        
                        for u,h in json_body['urls'].items():

                            soup = BeautifulSoup(h, "lxml")
                            
                            for link in soup.findAll('a'):
                                lnk = link.get('href')

                                if lnk is None or  lnk =='/':
                                    continue

                                if lnk[0]=='/':
                                    lnk=u+lnk

                                if any([lnk.find(domain) != -1 for domain in urls_domains]): # Check if the link is within the domain
                                    if all([lnk!=scrapped for scrapped in scrapped_urls]): # Check if it is not repeated
                                        urls.append(lnk)

                    else:
                        errors.append(body.decode())

                return levels

            except http_c.error as exc:
                errors.append(exc.args[0])
        raise ConnectionError("\n".join(errors))
        
    def build_json_string(self, urls:List[str])->str:
        """
        Builds the request json body given the urls
        """
        json_dict = {
            URLS_KEY: urls
        }
        return json.dumps(json_dict)

    def start(self, urls, deep_level: int) -> LEVEL_SCRAPING_DICT:
        
        try:
            return self.get_urls(urls,deep_level)

        except Exception as exc:
            raise exc
                


# fetch http://www.cubaeduca.cu http://www.etecsa.cu http://www.uci.cu http://evea.uh.cu http://www.uo.edu.cu http://www.uclv.edu.cu http://covid19cubadata.uh.cu http://www.uh.cu
