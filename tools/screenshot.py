#!/usr/bin/env python3
"""Render the EDOS main menu as it appears on the Atari, as a PNG.

    screenshot.py OUT.PNG [--xmem 512|256|0] [--scale 3]

Runs build/EDOS.COM from its start address on the emulated 6502 (sim.py)
with extended memory, drives D1 (fast/Speedy) and D2, and an emulation of
the OS screen editor (E:): cursor at ROWCRS/COLCRS, margins LMARGN/RMARGN,
clear screen, delete line, cursor moves, inverse video, and DSPFLG for
showing control characters. It stops when EDOS waits for the first key
and draws the 40x24 text screen in GRAPHICS 0 colours (COLOR2 background,
COLOR1 luminance) with a COLOR4 border. EDOS uses the ROM character set,
which is not available here; the image uses EREZ.FNT from
tools/disk/BASE.ATR, shifted to the ROM font's blank left column.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import Sim  # noqa: E402
import sparta  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROWS, COLS = 24, 40
ROWCRS, COLCRS, LMARGN, RMARGN = 0x54, 0x55, 0x52, 0x53
CRSINH, DSPFLG = 0x2F0, 0x2FE
COLOR1, COLOR2, COLOR4 = 0x2C5, 0x2C6, 0x2C8


class Editor:
    def __init__(self, sim):
        self.s = sim
        self.cells = [[0x20] * COLS for _ in range(ROWS)]

    def pos(self):
        return self.s.peek(ROWCRS), self.s.peek(COLCRS)

    def set(self, r, c):
        self.s.poke(ROWCRS, r)
        self.s.poke(COLCRS, c)

    def newline(self, r):
        r += 1
        if r >= ROWS:
            self.cells = self.cells[1:] + [[0x20] * COLS]
            r = ROWS - 1
        self.set(r, self.s.peek(LMARGN))

    def put(self, ch):
        r, c = self.pos()
        lm, rm = self.s.peek(LMARGN), self.s.peek(RMARGN)
        if not self.s.peek(DSPFLG):
            if ch == 0x7D:                                   # clear screen
                self.cells = [[0x20] * COLS for _ in range(ROWS)]
                return self.set(0, lm)
            if ch == 0x9B:                                   # EOL
                return self.newline(r)
            if ch == 0x9C:                                   # delete line
                del self.cells[r]
                self.cells.append([0x20] * COLS)
                return self.set(r, lm)
            moves = {0x1C: (-1, 0), 0x1D: (1, 0), 0x1E: (0, -1), 0x1F: (0, 1)}
            if ch in moves:
                dr, dc = moves[ch]
                return self.set((r + dr) % ROWS, min(max(c + dc, lm), rm))
        self.cells[r][c] = ch
        if c + 1 > rm:
            self.newline(r)
        else:
            self.set(r, c + 1)


def capture(xmem=512):
    bits = {512: 0x6E, 256: 0x6C, 0: 0x00}[xmem]
    s = Sim(bank_bits=bits)
    ed = Editor(s)

    def cio(sim, x):
        cmd = sim.peek(0x342 + x)
        if x == 0 and cmd in (0x09, 0x0B):
            buf, n = sim.word(0x344), sim.word(0x348)
            for k in range(n):
                ed.put(sim.peek(buf + k))
        return 1

    def sio(sim):
        st = sim.sio_log[-1]
        if st['cmd'] == 0x53:                                # status
            return 1 if st['unit'] <= 2 else 138
        if st['cmd'] == 0x3F:                                # Speedy high-speed index
            if st['unit'] == 1:
                sim.poke(st['buf'], 0x0A)
                return 1
            return 0x8B
        return 1
    s.cio_handler, s.sio_handler = cio, sio
    s.poke(0x2C5, 0xCA)                                      # OS default colours
    s.poke(0x2C6, 0x94)
    s.poke(0x9000, 0x60)                                     # DOS's DOSINI: RTS
    s.poke_word(0x0C, 0x9000)
    s.poke(LMARGN, 2)
    s.poke(RMARGN, 39)
    mpu = s.mpu
    mpu.sp, mpu.pc = 0xFD, s['PRE_START']
    for _ in range(5_000_000):
        if mpu.pc == s['GETCHR']:
            break
        if mpu.pc >= 0xD800 and s._trap():
            continue
        mpu.step()
    else:
        raise SystemExit("EDOS did not reach its menu prompt")
    return s, ed


def atari_rgb(colour):
    """approximate NTSC palette entry: hue 1 gold, 4 red, 9 blue, 12 green"""
    import colorsys
    hue, lum = colour >> 4, (colour & 0x0F) / 15
    if hue == 0:
        v = int(lum * 255)
        return (v, v, v)
    angle = (45 - (hue - 1) * 24) % 360
    r, g, b = colorsys.hls_to_rgb(angle / 360, 0.10 + lum * 0.75, 0.70)
    return (int(r * 255), int(g * 255), int(b * 255))


def render(sim, ed, path, scale=3):
    from PIL import Image
    d = sparta.Disk(os.path.join(ROOT, 'tools', 'disk', 'BASE.ATR'))
    e = d.find('EREZ.FNT')[1]
    font = bytearray(d.read_file(d.w(e, 1), 1024))
    # EREZ.FNT draws letters from column 0; the ROM font that EDOS really
    # uses leaves column 0 blank, which is what makes inverse letters look
    # like blocks. Shift glyphs whose column 7 is empty one pixel right.
    for g in range(128):
        rows = font[g * 8:g * 8 + 8]
        if not any(r & 1 for r in rows):
            font[g * 8:g * 8 + 8] = bytes(r >> 1 for r in rows)
    bg_c = sim.peek(COLOR2)
    bg = atari_rgb(bg_c)
    fg = atari_rgb((bg_c & 0xF0) | (sim.peek(COLOR1) & 0x0F))
    border = atari_rgb(sim.peek(COLOR4))
    bx, by = 16, 12
    w, h = COLS * 8 + 2 * bx, ROWS * 8 + 2 * by
    img = Image.new('RGB', (w, h), border)
    px = img.load()
    cur = None if sim.peek(CRSINH) else ed.pos()
    for r in range(ROWS):
        for c in range(COLS):
            ch = ed.cells[r][c]
            inv = bool(ch & 0x80) ^ (cur == (r, c))
            code = ch & 0x7F
            internal = code + 0x40 if code < 0x20 else code - 0x20 if code < 0x60 else code
            for y in range(8):
                bits = font[internal * 8 + y]
                for x in range(8):
                    on = bool(bits & (0x80 >> x)) ^ inv
                    px[bx + c * 8 + x, by + r * 8 + y] = fg if on else bg
    img = img.resize((w * scale * 2 // 2, h * scale), Image.NEAREST)
    img.save(path)
    return img.size


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('out')
    ap.add_argument('--xmem', type=int, default=512, choices=(0, 256, 512))
    ap.add_argument('--scale', type=int, default=3)
    a = ap.parse_args()
    sim, ed = capture(a.xmem)
    size = render(sim, ed, a.out, a.scale)
    text = '\n'.join(''.join(chr(ch & 0x7F) if 32 <= (ch & 0x7F) < 127 else '.' for ch in row)
                     for row in ed.cells)
    print(text)
    print(f"{a.out}: {size[0]}x{size[1]}")


if __name__ == '__main__':
    main()
