#!/usr/bin/env python3
"""The EDOS version (e.g. 3.3).

  version.py           the one in the title bar of build/EDOS.COM, as it
                       runs (on the simulated 6502)
  version.py --source  the one in TTL2 in EDOSVARS.M65 (inverse ATASCII)
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

if sys.argv[1:] == ['--source']:
    with open(os.path.join(HERE, '..', 'EDOSVARS.M65'), encoding='utf-8') as f:
        line = next(l for l in f if l.startswith('TTL2 '))
    title = ''.join(chr((ord(c) - 0xE000) & 0x7F) if 0xE000 <= ord(c) <= 0xE0FF else c for c in line)
else:
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
