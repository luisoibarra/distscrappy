"""
Start a Console DistScrappyClient connected to specified server in config.py
"""
from client.client import DistScrappyClient
import logging as log
from config import *

def start(*addresses:("Central nodes addresses")):
    log.basicConfig(level=log.INFO)

    curr_addresses = [(host ,int(port)) for host, port in [x.split(":") for x in addresses]]

    client = DistScrappyClient(curr_addresses if curr_addresses else [x for x, _, _ in SERVER_NS_ZMQ_ADDRS])

    command=""

    help_msg = "Availables commands:\n \
        fetch < depth_level:int > URL1 URL2 URL3 [...] \
        <This command will fetch listed urls and scrap to the level asigned>\n \
            exit <This command will terminate client process>\n \
                help <This command will show this help message>\n\
                     Example:\n fetch 0 www.wikipedia.org http://www.instagram.com"

    while True:
        command= input()
        if not command:
            print(help_msg)
            continue
        if command.lower() == "exit":
            break
        elif command.lower() == "help":
            print(help_msg)
        
        command,*args=command.split()

        if command.lower() == "fetch":
            result = client.start(args[1:], int(args[0]))
            print(result)
        else:
            print(help_msg)
        
             
            

if __name__ == "__main__":
    import plac
    plac.call(start)
