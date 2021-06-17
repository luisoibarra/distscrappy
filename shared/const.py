from typing import List,Dict,Tuple

# Common types
IP_DIR: Tuple[str, int] = Tuple[str, int]

# DHT Entry
# URL, Fetch Time, HTML.
URLState: Tuple[str, float, str] = Tuple[str, float, str]
ST_URL:int = 0
ST_FETCH_TIME:int = 1
ST_HTML:int = 2

def get_url_state(url:str, fetch_time:float, html:str) -> URLState:
    return (url, fetch_time, html)


# Scrapped Info
SCRAPPED_INFO: Tuple[str, str] = Tuple[str, str]  # Scrapped info HTML, Error in case of any.
SCR_HTML:int = 0
SCR_ERROR:int = 1

def get_scrapped_info(html:str, error:str) -> SCRAPPED_INFO:
    return (html, error)


# Dictionary mapping each URL to corresponding HTML
URLHTMLDict: Dict[str, SCRAPPED_INFO] = Dict[str, SCRAPPED_INFO]

ServerInfo: Tuple[IP_DIR, IP_DIR, IP_DIR] = Tuple[IP_DIR, IP_DIR, IP_DIR]
SERV_SERV : int = 0
SERV_NS : int = 1
SERV_ZMQ : int = 2


URLS_KEY : str = "urls" # Json key for URLs 
ERROR_KEY : str = "errors" # Json key for Errors

NS_TIME_RETRY:int = 10 #Name server retry time in seconds
