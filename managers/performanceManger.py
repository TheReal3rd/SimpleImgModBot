import time
import statistics

import globals

# AI but accidental. Like i asked AI something else and it produced a perfect class i needed so im taking it. :3 
# I don't see a reason to make it save the data. I may make it create graphs for lols but no more.
class PerformanceManager: # TODO Add graphs and extand data to include time and few more information. for lols.
    def __init__(self):
        self.metrics = {}
        self.result = {}

    def begin(self, operation: str):
        self.metrics[operation] = time.perf_counter()

    def start(self, operation: str):
        self.begin(operation)

    def stop(self, operation: str):
        self.end(operation)

    def end(self, operation: str):
        if operation not in self.metrics:
            return

        elapsed = time.perf_counter() - self.metrics[operation]

        globals.logger.info(
            f"[PERF] {operation}: {elapsed:.6f} sec"
        )
        
        if not operation in self.result.keys():
            self.result[operation] = []
        self.result[operation].append(elapsed)

        if len(self.result[operation]) >= 10:
            self.result[operation].pop(0)

        del self.metrics[operation]

    def fetchAll(self):
        return self.result

    def fetch(self, operation):
        return self.result[operation]

    def calcMedian(self, operation):
        if self._isEmpty() or not self._keyExists(operation):
            return -1

        sortedList = self.result[operation]
        return statistics.median(sortedList)

    def calcMean(self, operation):
        if self._isEmpty() or not self._keyExists(operation):
            return -1

        sortedList = self.result[operation]
        return statistics.fmean(sortedList)

    def calcMode(self, operation):
        if self._isEmpty() or not self._keyExists(operation):
            return -1

        sortedList = self.result[operation]
        return statistics.mode(sortedList)

    def _isEmpty(self):
        return len(self.result) <= 0

    def _keyExists(self, operation):
        return operation in self.result.keys()

    def summary(self):
        if self._isEmpty():
            return "No Data."

        result = ""
        for key in self.result.keys():
            result += f"{key} Median: {self.calcMedian(key):.2f} Mean: {self.calcMean(key):.2f} Mode: {self.calcMode(key):.2f}\n"
        return result
