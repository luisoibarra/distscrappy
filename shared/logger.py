import logging as log

class LoggerMixin:
    """
    Mixin that provides basic logging
    """
    
    def log_error(self, message:str):
        log.error(message)
        
    def log_info(self, message:str):
        log.info(message)
        
    def log_exception(self, exc:Exception):
        log.exception(exc)
        
    def log_debug(self, message:str):
        log.debug(message)