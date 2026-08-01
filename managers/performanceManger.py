import matplotlib.pyplot as plt

from time import perf_counter
from statistics import median, fmean, mode
from io import BytesIO

# Personal notes.
"""
Mean: Calculated by summing all values and dividing by the count; it is best for symmetric data without outliers but is sensitive to extreme values that can skew results. 


Median: The middle number in an ordered list; it is preferred for skewed distributions or data with outliers (e.g., income) because it is not affected by extreme values. 


Mode: The most occurring value; it is most useful for categorical or nominal data (e.g., most common shoe size) and can identify peaks in 
distribution where mean and median may be less informative. 
"""

# AI but accidental. Like i asked AI something else and it produced a perfect class i needed so im taking it. :3 
# I don't see a reason to make it save the data. I may make it create graphs for lols but no more.
class PerformanceManager:
    def __init__(self):
        self.metrics = {}
        self.result = {}

    def begin(self, operation: str):
        self.metrics[operation] = perf_counter()

    def start(self, operation: str):
        self.begin(operation)

    def stop(self, operation: str):
        self.end(operation)

    def end(self, operation: str):
        if operation not in self.metrics:
            return

        elapsed = perf_counter() - self.metrics[operation]

        if __name__ != "__main__":
            import globals
            globals.logger.info(
                f"[PERF] {operation}: {elapsed:.6f} sec"
            )
        else:
            print(f"[PERF] {operation}: {elapsed:.6f} sec")    
        
        if not operation in self.result.keys():
            self.result[operation] = []
        self.result[operation].append(elapsed)

        if len(self.result[operation]) >= 20:
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
        return median(sortedList)

    def calcMean(self, operation):
        if self._isEmpty() or not self._keyExists(operation):
            return -1

        sortedList = self.result[operation]
        return fmean(sortedList)

    def calcMode(self, operation):
        if self._isEmpty() or not self._keyExists(operation):
            return -1

        sortedList = self.result[operation]
        return mode(sortedList)

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

    def createGraph(self):
        if self._isEmpty():
            return None

        plt.figure(figsize=(9, 5))

        for ops, times in self.result.items():
            plt.plot(
                range(1, len(times) + 1),
                times,
                marker="o",
                label=ops,
            )

        plt.title("Execution Performance")
        plt.xlabel("Operations Runs")
        plt.ylabel("Execution Time (seconds)")
        plt.legend()
        plt.grid(True)

        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        plt.close()

        buffer.seek(0)

        return buffer

if __name__ == "__main__":
    import math
    import random

    testPerf = PerformanceManager()

    for ops in ["TestOp1", "TestOp2", "TestOp3"]:
        for times in range(0, 20):
            testPerf.start(ops)

            for x in range(random.randint(100000, 200000), 0, -1):
                if x <= 1:
                    break
                
                isPrime = True
                for i in range(2, int(math.sqrt(x)) + 1):
                    if x % i == 0:
                        isPrime = False
                        continue
                    
            testPerf.end(ops)

    print(testPerf.summary())

    testPerf.createGraph()