#!/usr/bin/env python3
"""Unit tests that run real EDOS machine code (build/EDOS.COM) under py65.

Run tools/build.sh first (it runs these tests too), or:
    python3 tools/test_edos.py -v
"""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import Sim, PORTB  # noqa: E402

EOL = 0x9B
SIO_RD, SIO_WT, SIO_SL = 0x52, 0x57, 0x68
ICCOM, ICBAL, ICBLL = 0x342, 0x344, 0x348


def pattern(sector, i):
    return (sector * 7 + i * 13 + (sector >> 8)) & 0xFF


class FakeDisk:
    """SIO stand-in: sectors filled with a per-sector pattern on read,
    captured on write. 128-byte sectors 1-3, `size` bytes after."""

    def __init__(self, size):
        self.size = size
        self.written = {}

    def __call__(self, sim):
        st = sim.sio_log[-1]
        if st['cmd'] == SIO_SL:
            return 0x8B                      # no fast-SIO drive
        n = st['size']
        expect = 128 if st['sector'] <= 3 else self.size
        assert n == expect, f"sector {st['sector']}: size {n}, expected {expect}"
        if st['cmd'] == SIO_RD:
            for i in range(n):
                sim.mem[st['buf'] + i] = pattern(st['sector'], i)
        elif st['cmd'] == SIO_WT:
            self.written[st['sector']] = bytes(sim.mem[st['buf'] + i] for i in range(n))
        return 1


class TestArithmetic(unittest.TestCase):
    def setUp(self):
        self.s = Sim()

    def test_calclen_carries_into_high_byte(self):
        s = self.s
        for start, end in [(0x2000, 0x20FF), (0x2000, 0x3FFF), (0x1234, 0x1234), (0x2080, 0x217F)]:
            s.poke_word(s['FILPOS'], start)
            s.poke_word(s['FILEND'], end)
            s.call('CALCLEN')
            self.assertEqual(s.word(s['FILLEN']), end - start + 1, f"{start:04X}-{end:04X}")

    def test_inp2addr(self):
        s = self.s
        for txt, val in [('2000', 0x2000), ('9C', 0x9C), ('', 0), ('BFFA', 0xBFFA),
                         ('A0', 0xA0), ('00', 0), ('FF', 0xFF), ('0123', 0x0123),
                         ('4567', 0x4567), ('89AB', 0x89AB), ('CDEF', 0xCDEF),
                         ('600', 0x600), ('5', 5), ('E00', 0xE00), ('12345', 0x1234)]:
            for k, c in enumerate(txt.encode() + bytes([EOL])):
                s.poke(s['INP1'] + k, c)
            s.call('INP2ADDR', y=len(txt))
            self.assertEqual(s.word(s['FILPOS']), val, txt)

    def test_copy(self):
        # JSR COPY / .WORD SRC,DST / LDA #$42 / RTS: copies through EOL,
        # Y = bytes copied, returns past the inline words
        s = self.s
        s.poke(0x5000, 0x20, s['COPY'] & 0xFF, s['COPY'] >> 8, 0x00, 0x51, 0x00, 0x52, 0xA9, 0x42, 0x60)
        s.poke(0x5100, *b'ABC', EOL, *b'XYZ')
        mpu = s.call(0x5000)
        self.assertEqual(bytes(s.mem[0x5200:0x5205]), b'ABC\x9b\x00')
        self.assertEqual((mpu.y, mpu.a), (4, 0x42))

    def test_fill(self):
        s = self.s
        f = s['FILL']
        for length, count in ((5, 5), (0, 256)):
            s.poke(0x5000, 0x20, f & 0xFF, f >> 8, 0x00, 0x51, length, 0x2A, 0x60)
            s.poke(0x5100, *bytes(258))
            mpu = s.call(0x5000, x=0x77)
            got = bytes(s.mem[0x5100:0x5100 + 258])
            self.assertEqual(got, b'*' * count + bytes(258 - count), length)
            self.assertEqual(mpu.x, 0x77)

    def test_hexout(self):
        s = self.s
        for v in (0, 0x09, 0x0A, 0x5F, 0x9A, 0xA0, 0xFF):
            mpu = s.call('HEXOUT', a=v, x=0x33, y=3)
            self.assertEqual(bytes(s.mem[s['FILE'] + 3:s['FILE'] + 5]).decode(), f"{v:02X}")
            self.assertEqual((mpu.y, mpu.x), (5, 0x33))


class TestErrorText(unittest.TestCase):
    def setUp(self):
        self.s = Sim()

    def text(self):
        s, out = self.s, ''
        for k in range(64):
            c = s.peek(s['FILE'] + k)
            if c == EOL:
                return out
            out += chr(c)
        self.fail("no EOL in FILE")

    def test_known_code(self):
        self.s.call('GETERRTXT', y=170)
        self.assertEqual(self.text(), 'File not found')

    def test_every_message(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'CIOSTAT.M65')).read()
        msgs = re.findall(r'\.BYTE (\d+),"([^"]*)",EOL', src)
        self.assertGreater(len(msgs), 20)
        for code, text in msgs:
            self.s.call('GETERRTXT', y=int(code))
            self.assertEqual(self.text(), text, code)

    def test_unknown_code_terminates(self):
        # used to scan past the table and hang or print garbage;
        # 134, 141, 145, 166 and 171 cannot happen in EDOS (no text)
        for code in (148, 150, 172, 200, 255, 134, 141, 145, 166, 171):
            self.s.call('GETERRTXT', y=code, max_steps=20_000)
            self.assertEqual(self.text(), '', code)


class TestDiskCopy(unittest.TestCase):
    """DSKCPY read then write through 256K of simulated banks."""

    def run_copy(self, density, sectors, size):
        s = Sim()
        disk = FakeDisk(size)
        s.sio_handler = disk
        s.poke(s['DSKNUM'], 1)
        s.poke(s['DENSITY'], density)
        s.poke_word(s['FSIOV'], 0)
        s.call('RSTSCTCNT')                  # COMDUP does this first
        s.call('DSKCPY', a=SIO_RD, max_steps=50_000_000)
        s.poke_word(s['FSIOV'], 0)
        s.call('RSTSCTCNT')
        s.call('DSKCPY', a=SIO_WT, max_steps=50_000_000)
        self.assertEqual(sorted(disk.written), list(range(1, sectors + 1)))
        bad = [n for n, data in disk.written.items()
               if data != bytes(pattern(n, i) for i in range(len(data)))]
        self.assertEqual(bad, [], f"sectors written back wrong: {bad[:12]}")
        self.assertEqual(s.peek(PORTB), s.peek(s['BANKS']), "main bank restored")

    def test_single_density(self):
        self.run_copy(1, 720, 128)

    def test_enhanced_density(self):
        self.run_copy(2, 1040, 128)

    def test_double_density(self):
        # used to lose the 2nd half of one sector per bank via $8000
        self.run_copy(3, 720, 256)


class TestSioCommands(unittest.TestCase):
    def test_format_commands(self):
        # @DOSIO with zero-page D2 used to send command $B7
        for density, cmd in ((2, 0x22), (1, 0x21)):
            s = Sim()
            s.poke(s['DSKNUM'], 1)
            s.call('FRMTDRV', a=density)
            self.assertEqual(s.sio_log[-1]['cmd'], cmd)


class TestInput(unittest.TestCase):
    """Drive COMANA (Analyze Sector) with scripted keyboard/editor input."""

    def make(self, typed):
        s = Sim()
        s.poke(s['DSKNUM'], 1)
        seen = {}

        def cio(sim, x):
            cmd = sim.peek(ICCOM + x)
            if cmd == 5:                               # get record (GETTEXT)
                buf = sim.word(ICBAL + x)
                limit = sim.peek(ICBLL + x)
                seen['limit'] = limit
                data = typed.encode() + bytes([EOL])
                n = min(len(data), limit)
                for k in range(n):
                    sim.poke(buf + k, data[k])
                sim.poke(ICBLL + x, n)
                return 1 if n == len(data) else 137     # truncated record
            if cmd == 7 and sim.word(ICBLL + x) == 0:  # GETCHR
                return (1, ord('N'))
            return 1
        s.cio_handler = cio
        return s, seen

    def run_until_getcom(self, s):
        # COMANA ends with JMP GETCOM; run it as a call and stop there
        mpu = s.mpu
        target = s['GETCOM']
        s.mpu.sp = 0xFD
        mpu.pc = s['COMANA']
        for _ in range(3_000_000):
            if mpu.pc == target:
                return
            if mpu.pc >= 0xD800 and s._trap():
                continue
            mpu.step()
        self.fail("COMANA did not reach GETCOM")

    def test_reads_typed_sector(self):
        # @SETSCT VALUE used to load the constant $B5/$B6 (sector 46773)
        s, _ = self.make('10')
        self.run_until_getcom(s)
        reads = [e['sector'] for e in s.sio_log if e['cmd'] == SIO_RD]
        self.assertIn(10, reads)
        self.assertNotIn(0xB6B5, reads)

    def test_sector_input_is_bounded(self):
        s, seen = self.make('1234567890123')
        # NUMBKS and FILEND sit right after the 5-byte SCTR
        guard = [s.peek(a) for a in range(s['SCTR'] + 5, s['SCTR'] + 8)]
        self.run_until_getcom(s)
        self.assertEqual(seen['limit'], 5)
        self.assertEqual(guard, [s.peek(a) for a in range(s['SCTR'] + 5, s['SCTR'] + 8)])


class TestFastSio(unittest.TestCase):
    """READFIO loads drive fast-SIO code only if it fits the FSIOV page."""

    def run_readfio(self, size):
        s = Sim()
        s.poke(s['DSKNUM'], 1)
        s.poke_word(s['FSIOV'], 0)

        def sio(sim):
            st = sim.sio_log[-1]
            if st['cmd'] == SIO_SL:                 # report code length
                sim.poke_word(st['buf'], size)
            return 1
        s.sio_handler = sio
        s.call('READFIO')
        return [e for e in s.sio_log if e['cmd'] == SIO_SL + 1]

    def test_fits_page(self):
        for size in (0x80, 0x100):
            loads = self.run_readfio(size)
            self.assertEqual(len(loads), 1, hex(size))
            self.assertEqual(loads[0]['buf'], Sim()['FSIOV'])
            self.assertEqual(loads[0]['size'], size)

    def test_too_big_is_skipped(self):
        for size in (0x101, 0x200, 0x400):
            self.assertEqual(self.run_readfio(size), [], hex(size))

    def run_fast(self, status, flags=0):
        """CALLSIO for a read with fast-SIO code at FSIOV returning status"""
        s = Sim()
        s.poke(s['FSIOV'], 0xA0, status, 0x60)        # LDY #status / RTS
        s.poke(s['DSKNUM'], 1)
        s.poke(s['DENSITY'], 1)
        s.poke(0x0302, SIO_RD)                         # DCOMND
        s.poke(0x0307, flags)                          # DUNUSE
        s.poke_word(0x030A, 5)                         # sector 5
        mpu = s.mpu
        s.poke_word(0x1FE, 0xFFF0 - 1)                 # sim.RETURN_TRAP
        mpu.sp, mpu.pc = 0xFD, s['CALLSIO']
        for _ in range(5000):
            if mpu.pc == 0xFFF0:
                return s, s.peek(0x0307)
            if mpu.pc == s['DISKERR']:
                return s, 'DISKERR'
            if mpu.pc >= 0xD800 and s._trap():
                continue
            mpu.step()
        self.fail('CALLSIO did not finish')

    def test_fast_sio_used_for_read(self):
        s, dunuse = self.run_fast(1)
        self.assertEqual(s.sio_log, [])                # SIOV not called
        self.assertEqual(dunuse, 0)

    def test_fast_sio_error_reported(self):
        s, dunuse = self.run_fast(0x90, flags=0x02)    # SKPERR: caller checks
        self.assertEqual(s.sio_log, [])
        self.assertEqual(dunuse, 0x80)                 # SIOERR

    def test_fast_sio_error_goes_to_diskerr(self):
        s, result = self.run_fast(0x90)
        self.assertEqual(result, 'DISKERR')

    def test_work_area_below_bank_window(self):
        s = Sim()
        self.assertLessEqual(s['END_PROG'], s['VAREND'])
        self.assertLessEqual(s['VAREND'], s['WRKBEG'])
        self.assertLessEqual(s['FSIOV'] + 0x100, 0x4000)


if __name__ == '__main__':
    unittest.main()
