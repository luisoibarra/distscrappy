from concurrent.futures import ThreadPoolExecutor, Future, CancelledError

from server.coordinator import Coordinator

from config import SERVER_NS_ZMQ_ADDRS

from typing import List

import zmq

import logging as log

log.basicConfig(level=log.DEBUG)

context = zmq.Context()
executor = ThreadPoolExecutor()
tasks:List[Future] = []
coordinators = []
for server,_1,_2 in SERVER_NS_ZMQ_ADDRS:
    others = list(set(SERVER_NS_ZMQ_ADDRS) - set([(server,_1,_2)]))
    coordinator = Coordinator(server, [x for x,_1,_2 in others], context, executor)
    tasks.append(executor.submit(coordinator.start))
    coordinators.append(coordinator)

while tasks:
    remove = []
    for t,c in zip(tasks,coordinators):
        if not t.running():
            try:
                print(t.exception(0))
            except TimeoutError:
                pass
            except CancelledError:
                pass
            except Exception as e:
                print(e)
            remove.append((t,c))
    for t,c in remove:
        coordinators.remove(c)
        tasks.remove(t)
        