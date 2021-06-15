import time

class ClockMixin:
    """
    Mixin that provides clock time methods
    """
    def initClockTime(self):
        self._clock_time_diff = 0

    def setClockTime(self, t : float):
        self._clock_time_diff = t - time.time()

    def getClockTime(self):
        return self._clock_time_diff + time.time()
