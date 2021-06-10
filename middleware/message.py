
class Message:
    """
    Base Message Class
    
    Used for comunication between nodes.
    """
    def __init__(self, sender_address:str, destination_address:str ,*args, **kwargs):
        self.sender_address = sender_address
        self.destination_address = destination_address
        self.args = args
        self.kwargs = kwargs