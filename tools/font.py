#!/usr/bin/env python3
"""Make EDOS.FNT, the character set EDOS loads at start, from EREZ.FNT.

EREZ.FNT (on tools/disk/BASE.ATR) draws its characters from pixel column
0. The Atari ROM font leaves column 0 blank, which is what keeps inverse
characters (EDOS's menu hotkeys) looking like solid blocks. Every glyph
whose column 7 is empty is therefore moved one pixel right; the few that
use all 8 columns stay as they are.

    font.py OUT.FNT
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sparta  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, 'tools', 'disk', 'BASE.ATR')


def erez_font():
    d = sparta.Disk(BASE)
    e = d.find('EREZ.FNT')[1]
    return d.read_file(d.w(e, 1), e[3] | e[4] << 8 | e[5] << 16)


def edos_font(src=None):
    font = bytearray(src if src is not None else erez_font())
    if len(font) != 1024:
        raise ValueError(f"font must be 1024 bytes, not {len(font)}")
    for g in range(128):
        rows = font[g * 8:g * 8 + 8]
        if not any(r & 1 for r in rows):
            font[g * 8:g * 8 + 8] = bytes(r >> 1 for r in rows)
    return bytes(font)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with open(sys.argv[1], 'wb') as f:
        f.write(edos_font())
