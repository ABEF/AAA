"""Cheap advancing read clock for the disposable Anvil lab, never live pricing."""
import time


class LocalChainClock:
    def __init__(self, read_timestamp, monotonic=time.monotonic):
        self.read_timestamp = read_timestamp
        self.monotonic = monotonic
        self.anchor = None

    def refresh(self):
        timestamp = self.read_timestamp()
        if type(timestamp) is not int or timestamp < 0:
            raise ValueError('Invalid local chain timestamp')
        self.anchor = (timestamp, self.monotonic())

    def __call__(self):
        if self.anchor is None:
            raise RuntimeError('Local chain clock has not been sampled')
        timestamp, sampled = self.anchor
        return timestamp + max(0, self.monotonic() - sampled)
