from middleware.message import Message
# TODO
class MessageComunicator:
    """
    Middleware class in charge of send and receive messages. 
    """
    def send_message(self, message:Message,**kwargs):
        """
        Send the message
        """
        pass
    
    def receive_message(self, address:str,**kwargs)->Message:
        """
        Receive a message on given address
        """
        pass
    
    def resolve_name(self, human_address:str)->str:
        """
        Resolve a human readable address into an actual address
        """
        pass
    