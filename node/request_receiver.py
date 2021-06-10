from node.base import Node
import http.server as http_s
import socketserver
import logging as log
import json
from typing import List,Dict,Tuple
from concurrent.futures import ThreadPoolExecutor, Future
import socket

URLS_KEY = "urls"

class MyHTTPServer(socketserver.ThreadingTCPServer):
    """
    My HTTP server
    """
    
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

    def _set_json_content(self, json_dict:Dict[str,str])->bytes:
        """
        Returns response content
        """
        content = json.dumps(json_dict)
        return content.encode("utf8")

    def _valid_request(self, request_json:str)->Tuple[Dict[str,str],str]:
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

        json_request, error = self._valid_request(get_data)
        
        content = None
        if error:
            self._set_headers(400) # Bad Request Code
            content = self._set_json_content({"error":error})
        else:
            try:
                htmls = self.solve_request(json_request)
                self._set_headers(200) # OK Code
                content = self._set_json_content(htmls)
            except Exception as exc:
                self._set_headers(500) # Server Error Code
                content = self._set_json_content({"error":exc.message})                

        self.wfile.write(content)

    def solve_request(self, request_json:Dict[str,str])->Dict[str,str]:
        """
        Return a dictionary containing all scrapped urls
        """
        dummy_json = {
            "www.here1.com": "html 1",
            "www.here2.com": "html 2",
        }
        # REAL THING GOES HERE
        return dummy_json

class HTTPRequestReceiverNode(Node):
    
    def __init__(self, direction, request_tcp_direction:str):
        """
        direction:  Inner node direction
        
        request_tcp_direction:  Listening tcp direction that clients should connect to in
        order to get the provided service.
        """
        
        super().__init__(direction)
        self.host, self.port = request_tcp_direction.split(":")
        self.port = int(self.port)
        self.server = None
    
    def start(self):
        with MyHTTPServer((self.host,self.port), ReceiverHandler) as server:
            log.info(f"Server listening on {self.direction}")
            self.server = server
            server.serve_forever()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()

