from concurrent.futures import ThreadPoolExecutor, Future, CancelledError
from server.coordinator import Coordinator
from config import SERVER_NS_ZMQ_ADDRS
from typing import List
import logging as log
from server.storage import StorageNode
from shared.const import *

data1 = {
    1:[
        ("url1", 1, "html1"),
        ("url2", 1, "html2"),
    ],
    2:[
        ("url3", 1, "html3"),
        ("url4", 1, "html4"),
    ]
}

data2 = {
    3:[
        ("url5", 1, "html5"),
        ("url6", 1, "html6"),
    ],
    6:[
        ("url7", 1, "html7"),
        ("url8", 1, "html8"),
    ],
}
log.basicConfig(level=log.DEBUG)

storage = StorageNode()

storage.save_entries(data1)
storage.save_entries(data2)

data1_fetched = storage.get_entries([1,2])

print("Data1\n",data1)
print("Data1 fetched\n",data1_fetched)
