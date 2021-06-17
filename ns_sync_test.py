from concurrent.futures import ThreadPoolExecutor, Future, CancelledError

from server.name_server_sync import NSSync

from config import SERVER_NS_ZMQ_ADDRS

from shared.const import *

from typing import List

import logging as log

log.basicConfig(level=log.DEBUG)

ns_sync = NSSync([x[SERV_NS] for x in SERVER_NS_ZMQ_ADDRS])

ns_sync.start()
