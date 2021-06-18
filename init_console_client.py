"""
Start a Console DistScrappyClient connected to specified server in config.py
"""
from client.client import DistScrappyClient
import logging as log
from config import *

def start():
    log.basicConfig(level=log.INFO)

    client = DistScrappyClient([x for x, _, _ in SERVER_NS_ZMQ_ADDRS])
    while True:
        
        command, urls = input().split(" ")
        if command.lower() == "fetch":
            result = client.start(urls)
            print(result)
        elif command.lower() == "exit":
            break
        elif command.lower() == "help":
            print('''Availables commands:\n
             fetch URL1 URL2 URL3 [...] \n
             exit\n
             help\n
             \n
            Example:\n 
             fetch www.wikipedia.org www.instagram.com''')
             
            

if __name__ == "__main__":
    start()
