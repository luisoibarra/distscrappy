import time

import Pyro4

@Pyro4.expose
class ClockMixin:
    """
    Mixin that provides clock time methods
    """
    def initClockTime(self):
        self._clock_time_diff = 0

    def setClockTime(self, t : float):
        if not hasattr(self, "__clock_time_diff"):
            self.initClockTime()

        self._clock_time_diff = t - time.time()

    def getClockTime(self):
        if not hasattr(self, "__clock_time_diff"):
            self.initClockTime()
        return self._clock_time_diff + time.time()
