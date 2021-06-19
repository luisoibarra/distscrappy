import Pyro4

# Pyro4.config.COMMTIMEOUT = 10 # Max amount of seconds to wait for a pyro conenction

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

# server address to deploy client fetched html
DEPLOY_SERVER_ADDR = ("127.0.0.3",9000)

# Test Storage node address
STORAGE_ADDR = ("127.0.0.4", 9000)

# Test http server
HTTP_TEST_SERVER_ADDR = ("127.0.0.5",9000)

# Cache valid time
CACHE_THRESHOLD_SECONDS = 60

# Write amount order to save state
WRITE_AMOUNT_SAVE_STATE = 1