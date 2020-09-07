# ticktock.py
"""Module used to measure execution time in simplistic way
"""
import time

class TickTock:
    __ticktock = float()
    @staticmethod
    def tick():
        TickTock.__ticktock = time.time()
    @staticmethod
    def tock():
        return time.time() - TickTock.__ticktock
