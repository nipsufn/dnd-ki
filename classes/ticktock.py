# ticktock.py
"""Module used to measure execution time in simplistic way
"""
import time

class TickTock:
    __ticktock = float()
    @staticmethod
    def tick():
        TickTock.__ticktock = time.perf_counter()
    @staticmethod
    def tock():
        return time.perf_counter() - TickTock.__ticktock
