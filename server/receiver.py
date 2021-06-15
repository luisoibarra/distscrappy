import http.server as http_s
import socketserver
import logging as log
import json
from typing import List,Dict,Tuple
from concurrent.futures import ThreadPoolExecutor, Future
import socket
from shared.http import HTTPRequest
from shared.const import *
from shared.logger import LoggerMixin


def valid_request(request_json:str)->Tuple[Dict[str,str],str]:
    """
    Returns an error message in case there are some problems with the request content.
    """
    final_json = None
    error_messages = []
    try:
        final_json = json.loads(request_json)
        if not URLS_KEY in final_json:
            error_messages.append(f"Missing key {URLS_KEY} in json body. This key is a list containing the urls to scrap")
    except Exception as exc:
        error_messages.append(exc.args[0])
    return final_json, "\n".join(error_messages)

class MyHTTPServer(socketserver.ThreadingTCPServer):
    """
    My HTTP server
    """
    
    def __init__(self, *args, **kwargs):
        self.central_node = kwargs.get("central_node", None)
        if self.central_node:
            kwargs.__delitem__("central_node")
            
        super().__init__(*args, **kwargs)
    
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()

class ReceiverHandler(http_s.BaseHTTPRequestHandler):
    """
    My Request handler
    """
    
    def _set_headers(self, code:int):
        """
        Set response headers
        """
        self.send_response(code)
        self.send_header("Content-type", "text/json")
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
        
        content_length = int(self.headers['Content-Length'])

        get_data = self.rfile.read(content_length)

        json_request, error = valid_request(get_data)
        
        content = None
        if error:
            self._set_headers(400) # Bad Request Code
            content = self._get_content(error)
        else:
            try:
                htmls = self.solve_request(json_request)
                self._set_headers(200) # OK Code
                content = self._get_content(htmls)
            except Exception as exc:
                self._set_headers(500) # Server Error Code
                content = self._get_content(exc.args[0])                

        self.wfile.write(content)

    def solve_request(self, request_json:Dict[str,str])->str:
        """
        Returns a json string with the response
        """
        response_json = {
            URLS_KEY : {},
            ERROR_KEY : {}
        }
        if self.server.central_node:
            info = self.server.central_node.get_urls(request_json[URLS_KEY])
            for key,(html,error) in info.items():
                if error:
                    response_json[ERROR_KEY][key] = error
                else:
                    response_json[URLS_KEY][key] = html
        return json.dumps(response_json)

class HTTPRequestReceiver(LoggerMixin):
    
    def __init__(self, receiver_address:IP_DIR):
        """
        request_tcp_direction:  Listening tcp direction that clients should connect to in
        order to get the provided service.
        """
        
        self.host, self.port = receiver_address
        self.server = None
    
    def start(self, central_node):
        with MyHTTPServer((self.host,self.port), ReceiverHandler, central_node=central_node) as server:
            self.log_info(f"Server listening on {self.host}:{self.port}")
            self.server = server
            server.serve_forever()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
