import os
import sys

path = os.path.split(os.path.dirname(__file__))[0]
sys.path.append(path)

import pytest
from node.request_receiver import HTTPRequestReceiverNode, URLS_KEY
import http
import json
from concurrent.futures import ThreadPoolExecutor, Future


@pytest.mark.parametrize("code, json_body", [
    (500, "NO JSON"),
    (200, json.dumps({URLS_KEY:["www.url1.com","www.url2.com"]})),
    (400, json.dumps({"NO VALID KEY":["www.url1.com","www.url2.com"]})),
])
def test_connection(code, json_body):
    host,port = "localhost",9003
    
    node = HTTPRequestReceiverNode("None",f"{host}:{port}" )
    executor = ThreadPoolExecutor()
    def connect():
        import time
        time.sleep(.5)
        
        a = http.client.HTTPConnection(host,port)
        
        content = json_body
        a.request("GET", "urls", content, {"Content-Length":len(content)})
        
        resp = a.getresponse()
        
        node.stop()
        assert resp.getcode() == code
        
    executor.submit(connect)
    node.start()    

if __name__ == "__main__":
    pytest.main()
    
    
    