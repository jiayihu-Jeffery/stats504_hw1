"""Mirror stdout to a text file so each script leaves a readable results log in its section's output folder."""
import sys


class _Tee:
    def __init__(self, *streams): self.streams = streams
    def write(self, s):
        for st in self.streams: st.write(s)
    def flush(self):
        for st in self.streams: st.flush()


def tee_to(path):
    sys.stdout = _Tee(sys.__stdout__, open(path, "w"))
