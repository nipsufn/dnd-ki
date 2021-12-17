# ticktock.py
"""Module used to measure execution time in simplistic way
"""
import time

class TickTock:
    """measure time between tic and toc calls"""
    __ticktock = []
    @staticmethod
    def tick():
        """mark start of measurement"""
        TickTock.__ticktock.append(time.perf_counter())
    @staticmethod
    def tock():
        """mark end of measurement"""
        try:
            return time.perf_counter() - TickTock.__ticktock.pop()
        except IndexError:
            return 0.0
