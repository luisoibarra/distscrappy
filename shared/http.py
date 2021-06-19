from http.server import BaseHTTPRequestHandler
from io import BytesIO


class HTTPRequest(BaseHTTPRequestHandler):
    """
    Parsing a HTTP request
    """
    
    def __init__ (self, request_bytes:bytes=None):
        if request_bytes:
            self.rfile = BytesIO(request_bytes)
            self.raw_requestline = self.rfile.readline()
            self.error_code = self.error_message = None
            self.parse_request()

    def send_error(self, code, message):
        """
        Sets error_code and error_message in case of a parsing error
        """
        self.error_code = code
        self.error_message = message

    @staticmethod
    def build_http_response(code:int=200, status_message:str="OK", headers:dict={}, content:str="")->bytes:
        """
        Builds a http response message
        """
        response = f"HTTP/1.1 {code} {status_message}\r\n"
        for key in headers:
            response += f"{key}: {headers[key]}\r\n"
        if not "Content-Lenght" in headers:
            response += f"Content-Length: {len(content)}\r\n"
        response += f"\r\n{content}"
        return response.encode()
    
    @staticmethod
    def build_http_request(method:str, url:str, headers:dict={}, content:str="")->bytes:
        """
        Builds a http request message
        """
        request = f"{method} {url} HTTP/1.1\r\n"
        for key in headers:
            request += f"{key}: {headers[key]}\r\n"
        if not "Content-Lenght" in headers:
            request += f"Content-Length: {len(content)}\r\n"
        request += f"\r\n{content}"
        return request.encode()

class HTTPResponse:
    
    def __init__(self, response:bytes):
        self.raw_response = response
        self.version = None
        self.status_code = None
        self.status_message = None
        self.headers = None
        self.data = None
        self.error_message = None
        self.parse()
        
    def parse(self):
        try:
            str_response = self.raw_response.decode()
            lines = str_response.split("\r\n")
            http, status_code, status_message = lines[0].split()
            self.version = http
            self.status_code = int(status_code)
            self.status_message = status_message
            headers = {}
            self.headers = headers
            data = b""
            next_is_data = False
            for line in lines[1:]:
                if line and not next_is_data:
                    header_key, value = line.split(":")
                    headers[header_key] = value
                elif not line:
                    next_is_data = True
                elif next_is_data:
                    data = line
            self.data = data
        except Exception as exc:
            self.error_message = exc.args[0]

# USAGE

# r = HTTPRequest(b"GET / HTTP/1.1\r\nContent-Length: 10\r\n1234567890")

# print(r.command)
# print(r.path)
# print(r.error_message)
# print(r.headers)
