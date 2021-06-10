class Node:
    """
    Base node class
    """
    
    def __init__(self, direction:str):
        """
        direction:  Inner node direction
        """
        self.direction = direction
        
    def start(self):
        raise NotImplementedError()
