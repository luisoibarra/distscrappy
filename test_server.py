import http.server as http_s
import socketserver
import logging as log
from typing import List,Dict,Tuple
from config import *
from server.receiver import MyHTTPServer
from concurrent.futures import ThreadPoolExecutor, Future
import os
import sys

test_server_dir = HTTP_TEST_SERVER_ADDR
base_dir = "html"
htmls = os.listdir(base_dir)

log.basicConfig()

class TestHandler(http_s.BaseHTTPRequestHandler):
    
    
    def _set_headers(self, code:int):
        """
        Set response headers
        """
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def _get_content(self, content:str)->bytes:
        """
        Returns response content
        """
        return content.encode("utf8")
    
    def do_GET(self):
        """
        Handles GET Request to server.
        
        Returns:
        200 -> All ok
        400 -> Bad Request
        500 -> Server Error
        """
        
        # content_length = int(self.headers['Content-Length'])

        # get_data = self.rfile.read(content_length)

        # json_request, error = valid_request(get_data)
        
        # content = None
        # if error:
        #     self._set_headers(400) # Bad Request Code
        #     content = self._get_content(error)
        # else:
        #     try:
        #         htmls = self.solve_request(json_request)
        #         self._set_headers(200) # OK Code
        #         content = self._get_content(htmls)
        #     except Exception as exc:
        #         self._set_headers(500) # Server Error Code
        #         content = self._get_content(exc.args[0])                

        log.info("Request received")
        self._set_headers(200)
        html = ""
        with open(os.path.join(base_dir,htmls[0])) as file:
            html = file.read()
        content = self._get_content(html)
        self.wfile.write(content)
        log.info("Request sent")

def start_test_server():
    with MyHTTPServer(test_server_dir, TestHandler) as server:
        server.serve_forever()
        
start_test_server()