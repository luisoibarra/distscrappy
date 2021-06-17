from typing import List,Dict,Tuple

# Common types
IP_DIR = Tuple[str,int]

# DHT Entry
URLState = Tuple[str, float, str] # URL, Fetch Time, HTML.
ST_URL = 0
ST_FETCH_TIME = 1
ST_HTML = 2

def get_url_state(url:str, fetch_time:float, html:str):
    return (url, fetch_time, html)

# Scrapped Info
SCRAPPED_INFO = Tuple[str,str] # Scrapped info HTML, Error in case of any.
SCR_HTML = 0
SCR_ERROR = 1

def get_scrapped_info(html:str, error:str) -> SCRAPPED_INFO:
    return (html, error)

URLHTMLDict = Dict[str,SCRAPPED_INFO] # Dictionary mapping each URL to corresponding HTML

ServerInfo = Tuple[IP_DIR,IP_DIR,IP_DIR]
SERV_SERV=0
SERV_NS=1
SERV_ZMQ=2


URLS_KEY = "urls" # Json key for URLs 
ERROR_KEY = "errors" # Json key for Errors