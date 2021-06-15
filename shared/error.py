class DistscrappyError(Exception):

    @property
    def message(self):
        return self.args[0]

class ScrapperError(DistscrappyError):
    pass