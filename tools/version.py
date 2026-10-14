#!/usr/bin/env python3
"""Print the EDOS version shown in the title bar of build/EDOS.COM (e.g. 2.8)."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import Sim  # noqa: E402

s = Sim()
a, title = s['TTL2'], ''
while s.peek(a) != 0x9B:
    title += chr(s.peek(a) & 0x7F)
    a += 1
m = re.search(r'EDOS (\d+\.\d+)', title)
if not m:
    sys.exit(f"no version in title {title!r}")
print(m.group(1))
