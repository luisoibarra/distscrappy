"""
Start a Console DistScrappyClient connected to specified server in config.py
"""
from client.client import DistScrappyClient
import logging as log
from config import *

def start():
    log.basicConfig(level=log.INFO)

    client = DistScrappyClient([x for x, _, _ in SERVER_NS_ZMQ_ADDRS])

    command=""

    help_msg = "Availables commands:\n fetch URL1 URL2 URL3 [...] <This command will fetch listed urls>\n exit <This command will terminate client process>\n help <This command will show this help message>\n Example:\n fetch www.wikipedia.org www.instagram.com"

    while True:
        command= input()
        if command.lower() == "exit":
            break
        elif command.lower() == "help":
            print(help_msg)
        
        command,*args=command.split(" ")

        if command.lower() == "fetch":
            result = client.start(args)
            print(result)
        else:
            print(help_msg)
        
             
            

if __name__ == "__main__":
    start()