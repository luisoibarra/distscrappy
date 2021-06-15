import plac
import os
import Pyro4 as pyro
from Pyro4.naming import NameServerDaemon

def init_name_server(ns_host:str=None, ns_port:int=0):
    daemon = NameServerDaemon(ns_host, ns_port)
    daemon.requestLoop()

def main(ns_host:("Pyro name server host","option","nsh",str)=None,
         ns_port:("Pyro name server port","option","nsp",int)=None):
    args = ["python3", "-m", "Pyro4.naming"]
    if ns_host != None and ns_port != None:
        args.extend(["-n", ns_host, "-p", str(ns_port)])
    os.execvp("python3",args)
    
if __name__ == "__main__":
    plac.call(main)