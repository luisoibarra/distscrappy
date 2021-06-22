# import Pyro4

# Pyro4.config.COMMTIMEOUT = 10 # Max amount of seconds to wait for a pyro connection

# Central node static addresses
SERVER_NS_ZMQ_ADDRS = [
    (("127.0.0.1",9000), ("127.0.0.1",9010), ("127.0.0.1",9020)),
    (("127.0.0.1",9001), ("127.0.0.1",9011), ("127.0.0.1",9021)),
    (("127.0.0.1",9002), ("127.0.0.1",9012), ("127.0.0.1",9022)),
]

# Test ring node addresses
RING_ADDRS = [
    ("127.0.0.2",9002),
    ("127.0.0.2",9003),
    ("127.0.0.2",9004),
    ("127.0.0.2", 9005),
    ("127.0.0.2", 9006),
    ("127.0.0.2", 9007),

]

# Hash bits for DHT. Max amount is 2^RING_BITS
RING_BITS = 5

# server address to deploy client fetched html
DEPLOY_SERVER_ADDR = ("127.0.0.3",9000)

# Test Storage node address
STORAGE_ADDR = ("127.0.0.4", 9000)

# Test http server
HTTP_TEST_SERVER_ADDR = ("127.0.0.5",9000)

# Cache valid time
CACHE_THRESHOLD_SECONDS = 256

# Clock syncronization delay
CLOCK_SYNC_DELAY_SECONDS = 40

# Register delay for storage node sync with name servers
STORAGE_NS_SYNC_DELAY_SECONDS = 60

# Write amount needed to save node state
WRITE_AMOUNT_SAVE_STATE = 10