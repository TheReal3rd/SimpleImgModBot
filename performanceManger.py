import time

# AI but accidental. Like i asked AI something else and it produced a perfect class i needed so im taking it. :3 
class PerformanceManager: # TODO add saving of this data into a DB.
    def __init__(self):
        self.metrics = {}

    def begin(self, operation: str):
        self.metrics[operation] = time.perf_counter()

    def end(self, operation: str):
        if operation not in self.metrics:
            return

        elapsed = time.perf_counter() - self.metrics[operation]

        print(
            f"[PERF] {operation}: "
            f"{elapsed:.6f} sec"
        )

        del self.metrics[operation]