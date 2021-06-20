import sqlite3
import plac
import Pyro4 as pyro
from Pyro4.naming import NameServerDaemon
from Pyro4.naming_storage import SqlStorage
import os.path as path
import os

def init_name_server(ns_host:str=None, ns_port:int=0, return_daemon=False):
    try:
        os.mkdir("data")
    except FileExistsError:
        pass
    filename = os.path.join("data",f"ns_data_{ns_host}_{ns_port}.sql")
    if not path.isfile(filename):
        fd = open(filename, 'x')
        fd.close()
    daemon = NameServerDaemon(ns_host, ns_port,storage=f"sql:{filename}")
    if return_daemon:
        return daemon
    daemon.requestLoop()

def main(ns_host:("Pyro name server host","option","nsh",str)=None,
         ns_port:("Pyro name server port","option","nsp",int)=None):

    try:
        os.mkdir("data")
    except FileExistsError:
        pass
    filename = os.path.join("data",f"ns_data_{ns_host}_{ns_port}.sql")
    args = ["python3", "-m", "Pyro4.naming"]
    if ns_host != None and ns_port != None:
        args.extend(["-n", ns_host, "-p", str(ns_port),"-s",f"sql:{filename}"])
    os.execvp("python3",args)
    
if __name__ == "__main__":
    plac.call(main)
