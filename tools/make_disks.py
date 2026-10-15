#!/usr/bin/env python3
"""Build SpartaDOS disk images from tools/disk/BASE.ATR.

BASE.ATR holds the SpartaDOS boot code, SpartaDOS 3.2 (X32G.DOS) and the
utilities that go on the EDOS disk; nothing EDOS-specific.

  build/EDOS.FNT      EDOS's character set (tools/font.py), loaded at start
  build/EDOS.ATR      the EDOS disk: BASE.ATR's files, build/EDOS.COM, EDOS.FNT and
                      the current sources in MAC/65 tokenized form
                      (LOAD #D:EDOS.M65)
  build/EDOSTEST.ATR  bootable test disk: SpartaDOS, EDOS.COM, the test
                      files used by tools/test_commands.py, RUNME.COM and
                      TESTPLAN.TXT (manual test steps for the real Atari)

Both are written as fresh file systems (tools/sparta.py) and checked with
fsck; every file is read back and compared.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sparta  # noqa: E402
import mac65tok  # noqa: E402
from font import edos_font  # noqa: E402
from test_commands import PROG, NORUN, TEXT, BIG, binfile  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, 'build')
SOURCE = os.path.join(ROOT, 'tools', 'disk', 'BASE.ATR')
DOS = 'X32G.DOS'
SOURCES = ['EDOS.M65', 'EDOSVARS.M65', 'MACROS.M65', 'SYSTEM.M65', 'UTILS.M65', 'CIOSTAT.M65']


def tokenized_sources():
    out = []
    for name in SOURCES:
        with open(os.path.join(ROOT, name), encoding='utf-8') as f:
            out.append((name, mac65tok.tokenize(f.read())))
    return out

# RUNME.COM: INIT stores $5A at $5300; RUN sets the background colour
# (COLOR4) to red and returns to DOS through DOSVEC.
RUNME = binfile((0x5000, bytes([0xA9, 0x34, 0x8D, 0xC8, 0x02, 0x6C, 0x0A, 0x00])),
                (0x5200, bytes([0xA9, 0x5A, 0x8D, 0x00, 0x53, 0x60])),
                run=0x5000, init=(0x5200, 0x5200))


def symbols():
    out = {}
    for line in sparta._read(os.path.join(BUILD, 'EDOS.SYM')).decode().splitlines():
        k, v = line.split()
        out[k] = int(v[1:], 16)
    return out


def plan(sym, nfiles):
    size = sym['END_PROG'] - sym['START_PROG'] + 12
    text = f"""EDOS 2.9 TEST PLAN
==================
D1: this disk (boot it, then EDOS).
D2: a blank formatted disk.
Answers are typed; Y/N are keys.
Expect: what you should see.

-- MENU / DIR --
1 Boot, run EDOS. Expect title
  EDOS 2.9, D:12 (or your drives),
  XMEM size, full menu.
2 F, RETURN. Expect D1 listing,
  Number of files: {nfiles}.
3 F, *.COM. Expect only .COM files.
4 Press 2. Expect D2 listing.
5 Press Z. Expect nothing happens.

-- LOAD / SAVE --
6 L PROG.COM, N. M 5300: first
  byte 5A (INIT ran). M 5000:
  01 02 03 04 05 06 07 08.
7 L NORUN.COM. Expect no Run
  prompt. M 5000: 41 42 43 44.
8 L TEXT.TXT. Expect
  Not a binary file!
9 L NOPE.COM. Expect
  * Error 170 File not found
10 L RUNME.COM, Y. Expect DOS
  prompt with red background.
  Run EDOS again.
11 S D2:OUT.COM 5000 50FF 5000.
  Then B PROG.COM D2:OUT.COM:
  Files are different. L D2:OUT
  .COM N: loads without error.
12 S D2:X.COM 50FF 5000 RETURN.
  Expect Invalid address!

-- COPY / COMPARE --
13 C *.* 2. Expect each file
  listed. B PROG.COM D2:PROG.COM:
  Files are the same.
14 C BIG.DAT 2 (20000 bytes, 2
  banks). B BIG.DAT D2:BIG.DAT:
  Files are the same.
15 C TEXT.TXT Y. Expect Insert
  Target [Y], then Read source.
16 B PROG.COM PROG2.COM: same.
  B PROG.COM NORUN.COM: different.
  B TEXT.TXT BIG.DAT: different.

-- FILES (on D2) --
17 R D2:TEXT.TXT NEW.TXT Y.
  F D2:: NEW.TXT, no TEXT.TXT.
18 P D2:*.COM. F D2:: * marks.
  U D2:PROG.COM: only it unlocked.
19 E D2:NEW.TXT Y: gone.
  E D2:BIG.DAT N: still there.

-- VIEW --
20 V TEXT.TXT 0010. First row
  0010-34 35 36 37 38 39 9B 48
  Y shows 0090-, N ends.
21 M 5000: shows Low/High memory,
  5000- row; + next 128, - back.
  M 600: first row is 0600-.
22 A 10: Sector: 10. + shows 11,
  - shows 10, N ends.

-- DISK (uses D2!) --
23 D, Y (reads D1), 2. Copies all
  sectors to D2. F D2:: same as
  D1.
24 N 2, then I 1 (Single), Y.
  F: D2 is empty. N 1 back.
25 N 2: drive 2 highlighted.
  N 5 (no drive): stays.

-- PROGRAM --
26 W Y: writes EDOS.COM to the
  current drive ({size} bytes).
27 G 5000 after L RUNME.COM N:
  red background, DOS prompt.
28 T: no cartridge -> menu;
  with BASIC -> READY.
29 Q: DOS prompt. Press RESET:
  stays in DOS.
30 In EDOS press RESET: EDOS menu
  comes back.
31 Esc at any prompt: back to
  the menu.

-- FONT --
32 EDOS shows the EDOS.FNT font
  (inverse hotkeys as blocks).
  Q: DOS uses the ROM font again.
33 RENAME EDOS.FNT X.FNT, run
  EDOS: ROM font, no error.
  RENAME X.FNT EDOS.FNT after.
"""
    return text.replace('\n', '\x9b').encode('latin1')


def make(path, volume, files, boot_file):
    d = sparta.new_disk(path, SOURCE, volume)
    for name, data, *stamp in files:
        d.add(name, data, stamp=stamp[0] if stamp else None)
    d.set_boot_file(boot_file)
    d.save()
    d = sparta.Disk(path)
    problems, lost = d.fsck()
    if problems or lost:
        raise SystemExit(f"{path}: fsck failed: {problems} {lost}")
    for name, data, *_ in files:
        f = d.find(name)
        e = f[1]
        if d.read_file(d.w(e, 1), e[3] | e[4] << 8 | e[5] << 16) != data:
            raise SystemExit(f"{path}: {name} reads back wrong")
    free = d.w(d.read(1), 0x0D)
    print(f"{os.path.relpath(path, ROOT)}: {len(files)} files, {free} free sectors")


def main():
    src = sparta.Disk(SOURCE)
    edos = sparta._read(os.path.join(BUILD, 'EDOS.COM'))
    originals = []
    for i, e in src.entries():
        if src.live(e) and not e[0] & 0x20:
            name = src.name(e)
            data = src.read_file(src.w(e, 1), e[3] | e[4] << 8 | e[5] << 16)
            originals.append((name, data, bytes(e[17:23])))
    names = [n for n, *_ in originals]
    if DOS not in names:
        raise SystemExit(f"{SOURCE}: {DOS} not found")

    orig = {n: (d, st) for n, d, st in originals}
    files = [(DOS,) + orig[DOS]]
    fnt = edos_font()
    with open(os.path.join(BUILD, 'EDOS.FNT'), 'wb') as f:
        f.write(fnt)
    files.append(('EDOS.COM', edos))
    files.append(('EDOS.FNT', fnt))
    files += tokenized_sources()
    for name, data, stamp in originals:
        if name in (DOS, 'EDOS.COM') or name in SOURCES:
            continue
        files.append((name, data, stamp))
    make(os.path.join(BUILD, 'EDOS.ATR'), 'EDOS', files, DOS)

    test = [(DOS,) + orig[DOS], ('EDOS.COM', edos), ('EDOS.FNT', fnt),
            ('PROG.COM', PROG), ('PROG2.COM', PROG), ('NORUN.COM', NORUN),
            ('TEXT.TXT', TEXT), ('BIG.DAT', BIG), ('RUNME.COM', RUNME),
            ('TESTPLAN.TXT', b'')]
    test[-1] = ('TESTPLAN.TXT', plan(symbols(), len(test)))
    make(os.path.join(BUILD, 'EDOSTEST.ATR'), 'EDOSTEST', test, DOS)


if __name__ == '__main__':
    main()
