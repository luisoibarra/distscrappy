CENTRAL_ADDR = ("127.0.0.1",9001)
NS_ADDR = ("127.0.0.1",9000)

SERVER_AND_NS_ADDRS = [
    (("127.0.0.1",9000), ("127.0.0.1",9010)),
    (("127.0.0.1",9001), ("127.0.0.1",9011)),
    (("127.0.0.1",9002), ("127.0.0.1",9012)),
]

RING_ADDRS = [
    ("127.0.0.2",9002),
    ("127.0.0.2",9003),
    # ("127.0.0.2",9004),
]

HTTP_TEST_SERVER_ADDR = ("127.0.0.5",9000)
