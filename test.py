from server.central import CentralNode
from server.ring import RingNode
from client.client import DistcrappyClient
from concurrent.futures import ThreadPoolExecutor
import time

ns_dir = "127.0.0.1",9000
server_dir = "127.0.0.1",9001
ring1_dir = "127.0.0.2",9002

executor = ThreadPoolExecutor()

central = CentralNode(ns_dir, server_dir)
client = DistcrappyClient([server_dir])
ring1 = RingNode(ring1_dir[0], ring1_dir[1], ns_dir[0], ns_dir[1])

central_task = executor.submit(central.start)
ring1_taks = executor.submit(ring1.start)

time.sleep(.5)
client.get_urls(["http://dummy.com"])

print(task.result())