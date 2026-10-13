#!/usr/bin/env python3
"""Functional tests: every EDOS menu command, run on the emulated 6502.

Each test starts EDOS code at a command (or at the menu prompt) with a fake
DOS (files on D1:/D2:), scripted keys and typed lines, and a fake disk
drive, then checks the actual result: files written, memory loaded, sectors
copied, text on screen, or where control went (cartridge, run address,
DOS). Uses build/EDOS.COM and build/EDOS.SYM.

    python3 tools/test_commands.py -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import Sim, PORTB  # noqa: E402
from difftest import World, Done, symbolizer, binfile  # noqa: E402

EOL = 0x9B
RTS = 0x60


class Drive(World):
    """World with drives D1/D2 present and per-call density answers."""

    def __init__(self, *a, densities=(), **k):
        super().__init__(*a, **k)
        self.densities = list(densities)
        self.sio_cmds = []

    def sio(self, sim):
        st = sim.sio_log[-1]
        self.sio_cmds.append((st['cmd'], st['unit'], st['sector']))
        if st['cmd'] == 0x53 and st['unit'] <= 2:
            d = self.densities.pop(0) if self.densities else 1
            sim.poke(0x02EA, {1: 0, 2: 0x80, 3: 0x20}[d], 0, 0, 0)
            return 1
        return super().sio(sim)


class Machine:
    def __init__(self, files=None, keys='', lines=(), numbks=16, densities=()):
        self.sim = s = Sim()
        self.w = Drive(s, files or {}, keys, list(lines), symbolizer(s), densities=densities)
        s.cio_handler = self.w.cio
        s.sio_handler = self.w.sio
        s.poke(s['DSKNUM'], 1)
        s.poke(s['NUMBKS'], numbks)
        s.poke_word(s['RTNPTR'], s['GETCOM'])
        s.poke(s['STKPTR'], 0xFD)
        self.hits = {}

    def __getitem__(self, name):
        return self.sim[name]

    def run(self, entry, stop=('GETCOM',), a=0, watch=(), max_steps=20_000_000):
        """Run from entry until the PC reaches a stop address (not the entry
        itself on step 0). Returns the name/address of the stop reached."""
        s, mpu = self.sim, self.sim.mpu
        stops = {(s[x] if isinstance(x, str) else x): x for x in stop}
        watch = {(s[x] if isinstance(x, str) else x) for x in watch}
        mpu.sp, mpu.a = 0xFD, a
        mpu.pc = s[entry] if isinstance(entry, str) else entry
        try:
            for step in range(max_steps):
                pc = mpu.pc
                if pc in watch:
                    self.hits[pc] = self.hits.get(pc, 0) + 1
                if pc in stops and step:
                    return stops[pc]
                if pc >= 0xD800 and s._trap():
                    continue
                mpu.step()
        except Done as e:
            raise AssertionError(f"needed more input: {e}")
        raise AssertionError(f"no stop reached from {entry}")

    def close_files(self):
        for x in list(self.w.open):
            self.w.dos(x, 0x0C, 0, 0, 0)

    @property
    def screen(self):
        return ''.join('\n' if c == EOL else chr(c & 0x7F) if 32 <= (c & 0x7F) < 127 else '~'
                       for c in self.w.screen)

    def file(self, drive, name):
        f = self.w.files.get(drive, {}).get(name)
        return bytes(f[0]) if f else None

    def mem(self, addr, n):
        return bytes(self.sim.mem[addr + k] for k in range(n))

    def opened(self):
        return [dict(t[1]).get('name') for t in self.w.trace
                if t[0] == 'CIO' and dict(t[1])['cmd'] == 3]


def segments(data):
    out, i = [], 0
    while i < len(data):
        if data[i:i + 2] == b'\xff\xff':
            i += 2
        s, e = data[i] | data[i + 1] << 8, data[i + 2] | data[i + 3] << 8
        out.append((s, data[i + 4:i + 5 + e - s]))
        i += 5 + e - s
    return out


INIT_CODE = bytes([0xA9, 0x5A, 0x8D, 0x00, 0x53, RTS])        # LDA #$5A / STA $5300 / RTS
PROG = binfile((0x5000, bytes(range(1, 101))), (0x5200, INIT_CODE),
               run=0x5000, init=(0x5200, 0x5200))
NORUN = binfile((0x5000, b'ABCDEF'))
TEXT = b'HELLO WORLD 0123456789\x9b' * 20
BIG = bytes((i * 7) & 0xFF for i in range(20000))


def files(**extra):
    d = {1: {'PROG.COM': PROG, 'NORUN.COM': NORUN, 'TEXT.TXT': TEXT, 'BIG.DAT': BIG,
             'PROG2.COM': PROG}, 2: {'OTHER.DAT': b'xyz'}}
    for k, v in extra.items():
        d.setdefault(1, {})[k.replace('_', '.')] = v
    return d


class TestMenu(unittest.TestCase):
    KEYS = {'F': 'COMDIR', 'T': 'COMCAR', 'C': 'COMCPY', 'D': 'COMDUP', 'E': 'COMERA',
            'I': 'COMINI', 'V': 'COMVIE', 'A': 'COMANA', 'P': 'COMPRC', 'U': 'COMUNP',
            'R': 'COMREN', 'S': 'COMSAV', 'L': 'COMLOA', 'G': 'COMGOT', 'N': 'COMNEW',
            'M': 'COMMEM', 'B': 'COMCMP', 'W': 'COMWRT', 'Q': 'COMQIT', '\x9b': 'GOMENU'}

    def test_every_menu_key_dispatches(self):
        for key, target in self.KEYS.items():
            m = Machine(keys=key)
            self.assertEqual(m.run('GETCOM', stop=list(self.KEYS.values())), target, repr(key))

    def test_digits_list_that_drive(self):
        for d in '12345678':
            m = Machine(keys=d)
            self.assertEqual(m.run('GETCOM', stop=['COMDIG']), 'COMDIG')

    def test_unknown_key_is_ignored(self):
        m = Machine(keys='Z')
        self.assertEqual(m.run('GETCOM', stop=['GETCOM'] + list(self.KEYS.values())), 'GETCOM')

    def test_menu_screen(self):
        m = Machine()
        m.run('GOMENU')
        for text in ('EDOS 2.8', 'Dir D1-D8', 'Write EDOS', 'Copy Files', 'Duplicate Disk',
                     'Quit to DOS', 'XMEM:'):
            self.assertIn(text, m.screen)


class TestDirectory(unittest.TestCase):
    def test_lists_default_drive(self):
        m = Machine(files(), lines=[''])
        m.run('COMDIR')
        self.assertEqual(m.opened(), ['D1:*.*'])
        for n in ('PROG', 'TEXT', 'BIG', 'FREE SECTORS', 'Number of files: 5'):
            self.assertIn(n, m.screen)

    def test_digit_key_lists_other_drive(self):
        m = Machine(files(), keys='2')
        m.run('GETCOM', stop=['GETCOM'])          # GETCOM -> COMDIG -> listing -> GETCOM
        self.assertIn('D2:*.*', m.opened())
        self.assertIn('OTHER', m.screen)
        self.assertNotIn('PROG', m.screen)

    def test_pattern(self):
        m = Machine(files(), lines=['*.COM'])
        m.run('COMDIR')
        self.assertIn('PROG', m.screen)
        self.assertNotIn('TEXT', m.screen)


class TestLoadBinary(unittest.TestCase):
    def test_loads_segments_and_calls_init(self):
        m = Machine(files(), lines=['PROG.COM'], keys='N')
        m.run('COMLOA')
        self.assertEqual(m.mem(0x5000, 100), bytes(range(1, 101)))
        self.assertEqual(m.mem(0x5300, 1), b'\x5a', "INITAD routine not called")
        self.assertIn('Run Program', m.screen)

    def test_run_jumps_to_runad(self):
        m = Machine(files(), lines=['PROG.COM'], keys='Y')
        self.assertEqual(m.run('COMLOA', stop=['GETCOM', 0x5000]), 0x5000)

    def test_no_run_address_no_prompt(self):
        m = Machine(files(), lines=['NORUN.COM'])
        m.run('COMLOA')
        self.assertEqual(m.mem(0x5000, 6), b'ABCDEF')
        self.assertNotIn('Run Program', m.screen)

    def test_not_binary(self):
        m = Machine(files(), lines=['TEXT.TXT'])
        m.run('COMLOA')
        self.assertIn('Not a binary file', m.screen)

    def test_missing_file_error(self):
        m = Machine(files(), lines=['NOPE.COM'])
        m.run('COMLOA')
        self.assertIn('170', m.screen)
        self.assertIn('File not found', m.screen)


class TestSaveBinary(unittest.TestCase):
    def setUp(self):
        self.data = bytes((i * 5 + 3) & 0xFF for i in range(256))

    def save(self, lines):
        m = Machine(files(), lines=lines)
        m.sim.poke(0x5000, *self.data)
        m.run('COMSAV')
        m.close_files()
        return m

    def test_exact_file_with_run_address(self):
        m = self.save(['OUT.COM', '5000', '50FF', '5000'])
        self.assertEqual(m.file(1, 'OUT.COM'),
                         b'\xff\xff\x00\x50\xff\x50' + self.data + b'\xe0\x02\xe1\x02\x00\x50')

    def test_no_run_address(self):
        m = self.save(['OUT.COM', '5010', '501F', ''])
        self.assertEqual(m.file(1, 'OUT.COM'), b'\xff\xff\x10\x50\x1f\x50' + self.data[16:32])

    def test_rejects_end_before_start(self):
        m = self.save(['OUT.COM', '50FF', '5000', ''])
        self.assertIn('Invalid address', m.screen)
        self.assertIsNone(m.file(1, 'OUT.COM'))

    def test_saved_file_loads_back(self):
        m = self.save(['OUT.COM', '5000', '50FF', ''])
        m2 = Machine({1: {'OUT.COM': m.file(1, 'OUT.COM')}}, lines=['OUT.COM'])
        m2.run('COMLOA')
        self.assertEqual(m2.mem(0x5000, 256), self.data)


class TestWriteEdos(unittest.TestCase):
    def test_writes_loadable_copy_of_itself(self):
        m = Machine(files(), keys='Y')
        m.run('COMWRT')
        m.close_files()
        data = m.file(1, 'EDOS.COM')
        self.assertIsNotNone(data, "EDOS.COM not written")
        segs = segments(data)
        self.assertEqual(len(segs), 2)
        (start, body), (runad, vec) = segs
        self.assertEqual(start, m['START_PROG'])
        self.assertEqual(start + len(body), m['END_PROG'], "must end at END_PROG-1")
        self.assertEqual(body, m.mem(start, len(body)))
        self.assertEqual(runad, 0x02E0)
        self.assertEqual(vec[0] | vec[1] << 8, m['PRE_START'])

    def test_no_does_not_write(self):
        m = Machine(files(), keys='N')
        m.run('COMWRT')
        m.close_files()
        self.assertIsNone(m.file(1, 'EDOS.COM'))


class TestCopyFiles(unittest.TestCase):
    def test_wildcard_copy_to_d2(self):
        m = Machine(files(), lines=['D1:*.*'], keys='2')
        m.run('COMCPY')
        m.close_files()
        for n in ('PROG.COM', 'TEXT.TXT', 'BIG.DAT', 'NORUN.COM'):
            self.assertEqual(m.file(2, n), m.file(1, n), n)

    def test_same_drive_prompts_for_swaps(self):
        m = Machine(files(), lines=['TEXT.TXT'], keys='YYY')
        m.run('COMCPY')
        self.assertIn('Insert Target', m.screen)
        self.assertIn('Read source', m.screen)

    def test_same_drive_abort_at_swap(self):
        m = Machine(files(), lines=['TEXT.TXT'], keys='YN')
        m.run('COMCPY')
        self.assertIn('Insert Target', m.screen)
        self.assertNotIn('Read source', m.screen)

    def test_needs_extended_memory(self):
        m = Machine(files(), lines=['TEXT.TXT'], keys='2', numbks=0)
        m.run('COMCPY')
        m.close_files()
        self.assertIn('Not enough memory', m.screen)
        self.assertIsNone(m.file(2, 'TEXT.TXT'))

    def test_file_larger_than_banks(self):
        m = Machine(files(), lines=['BIG.DAT'], keys='2', numbks=1)
        m.run('COMCPY')
        m.close_files()
        self.assertIn('Not enough memory', m.screen)
        self.assertIsNone(m.file(2, 'BIG.DAT'))
        self.assertEqual(m.sim.peek(PORTB), m.sim.peek(m['BANKS']))


class TestCompare(unittest.TestCase):
    def check(self, a, b, expect):
        m = Machine(files(), lines=[a, b])
        m.run('COMCMP')
        self.assertIn(expect, m.screen)

    def test_same(self):
        self.check('PROG.COM', 'PROG2.COM', 'Files are the same')

    def test_different(self):
        self.check('PROG.COM', 'NORUN.COM', 'Files are different')

    def test_different_length(self):
        self.check('TEXT.TXT', 'BIG.DAT', 'Files are different')


class TestFileCommands(unittest.TestCase):
    def test_erase(self):
        m = Machine(files(), lines=['TEXT.TXT'], keys='Y')
        m.run('COMERA')
        self.assertIsNone(m.file(1, 'TEXT.TXT'))

    def test_erase_cancel(self):
        m = Machine(files(), lines=['TEXT.TXT'], keys='N')
        m.run('COMERA')
        self.assertIsNotNone(m.file(1, 'TEXT.TXT'))

    def test_rename(self):
        m = Machine(files(), lines=['TEXT.TXT', 'NEW.TXT'], keys='Y')
        m.run('COMREN')
        self.assertIsNone(m.file(1, 'TEXT.TXT'))
        self.assertEqual(m.file(1, 'NEW.TXT'), TEXT)

    def test_protect_unprotect(self):
        m = Machine(files(), lines=['PROG*.COM'])
        m.run('COMPRC')
        self.assertTrue(m.w.files[1]['PROG.COM'][1] and m.w.files[1]['PROG2.COM'][1])
        m.w.lines = ['PROG.COM']
        m.run('COMUNP')
        self.assertFalse(m.w.files[1]['PROG.COM'][1])
        self.assertTrue(m.w.files[1]['PROG2.COM'][1])


class TestViewers(unittest.TestCase):
    def test_view_file_at_offset(self):
        m = Machine(files(), lines=['TEXT.TXT', '0010'], keys='N')
        m.run('COMVIE')
        row = ' '.join(f"{b:02X}" for b in TEXT[16:24])
        self.assertIn('0010-' + row, m.screen)

    def test_view_more(self):
        m = Machine(files(), lines=['TEXT.TXT', '0000'], keys='YN')
        m.run('COMVIE')
        self.assertIn('0080-' + ' '.join(f"{b:02X}" for b in TEXT[128:136]), m.screen)

    def test_memory_view_and_paging(self):
        m = Machine(lines=['5000'], keys='+N')
        m.sim.poke(0x5000, *range(256))
        m.run('COMMEM')
        self.assertIn('5000-00 01 02 03 04 05 06 07', m.screen)
        self.assertIn('5080-80 81 82 83 84 85 86 87', m.screen)

    def test_analyze_sector_navigation(self):
        m = Machine(lines=['10'], keys='+-N')
        m.run('COMANA')
        reads = [sec for cmd, unit, sec in m.w.sio_cmds if cmd == 0x52 and sec != 0x10]
        self.assertEqual(reads, [10, 11, 10])
        self.assertIn('Sector: 10', m.screen)


class TestDisk(unittest.TestCase):
    def test_duplicate_same_drive_all_sectors(self):
        for density, count, size in ((1, 720, 128), (3, 720, 256)):
            m = Machine(keys='YY', densities=[density, density])
            m.run('COMDUP', max_steps=60_000_000)
            written = {s: d for (u, s), d in m.w.disk.items()}
            self.assertEqual(sorted(written), list(range(1, count + 1)), density)
            bad = [s for s, d in written.items()
                   if d != bytes((s * 7 + i * 13) & 0xFF for i in range(len(d)))]
            self.assertEqual(bad, [], density)

    def test_duplicate_formats_on_density_mismatch(self):
        m = Machine(keys='YY', densities=[1, 3])
        m.run('COMDUP', max_steps=60_000_000)
        cios = [dict(t[1])['cmd'] for t in m.w.trace if t[0] == 'CIO']
        self.assertIn(0xFE, cios, "target not formatted")

    def test_duplicate_needs_memory(self):
        m = Machine(keys='YY', numbks=4, densities=[1])
        m.run('COMDUP')
        self.assertIn('Not enough memory', m.screen)

    def test_initialize_single(self):
        m = Machine(files(), keys='1Y')
        m.run('COMINI')
        self.assertIn(0x4F, [c for c, u, s in m.w.sio_cmds])           # PERCOM written
        self.assertIn(0xFE, [dict(t[1])['cmd'] for t in m.w.trace if t[0] == 'CIO'])
        self.assertEqual(m.w.files[1], {})

    def test_initialize_enhanced(self):
        m = Machine(keys='2Y')
        m.run('COMINI')
        cmds = [(c, s) for c, u, s in m.w.sio_cmds]
        self.assertIn(0x22, [c for c, s in cmds])
        self.assertIn((0x57, 360), cmds)                                 # VTOC
        self.assertIn((0x57, 1024), cmds)                                # VTOC2

    def test_initialize_cancel(self):
        m = Machine(files(), keys='1N')
        m.run('COMINI')
        self.assertNotIn(0x22, [c for c, u, s in m.w.sio_cmds])
        self.assertTrue(m.w.files[1])

    def test_new_drive(self):
        m = Machine(keys='2')
        m.run('COMNEW')
        self.assertEqual(m.sim.peek(m['DSKNUM']), 2)
        self.assertEqual(chr(m.sim.peek(m['DISK'] + 1)), '2')

    def test_new_drive_rejects_missing_drive(self):
        m = Machine(keys='5')
        m.run('COMNEW')
        self.assertEqual(m.sim.peek(m['DSKNUM']), 1)


class TestExits(unittest.TestCase):
    """Commands that leave EDOS must hand DOSINI back first."""

    def setUp(self):
        self.m = Machine()
        s = self.m.sim
        s.poke_word(s['DOSIN'], 0x1234)               # DOS's own DOSINI
        s.poke_word(0x0C, s['START'])                 # EDOS hooked in

    def dosini(self):
        return self.m.sim.word(0x0C)

    def test_quit(self):
        self.m.sim.poke_word(0x0A, 0xA100)            # DOSVEC
        self.assertEqual(self.m.run('COMQIT', stop=['GETCOM', 0xA100]), 0xA100)
        self.assertEqual(self.dosini(), 0x1234)

    def test_goto_address(self):
        self.m.w.lines = ['A123']
        self.assertEqual(self.m.run('COMGOT', stop=['GETCOM', 0xA123]), 0xA123)
        self.assertEqual(self.dosini(), 0x1234)

    def test_cartridge(self):
        s = self.m.sim
        s.poke(0x06, 1)                               # TRAMSZ: cartridge present
        s.poke_word(0xBFFA, 0xA200)
        self.assertEqual(self.m.run('COMCAR', stop=['GETCOM', 0xA200]), 0xA200)
        self.assertEqual(self.dosini(), 0x1234)

    def test_no_cartridge(self):
        self.m.sim.poke(0x06, 0)
        self.assertEqual(self.m.run('COMCAR'), 'GETCOM')
        self.assertEqual(self.dosini(), self.m['START'])


class TestStartAndReset(unittest.TestCase):
    def test_first_start_hooks_dosini_and_reset_reenters(self):
        m = Machine()
        s = m.sim
        s.poke(0x9000, RTS)                           # DOS's reset handler
        s.poke_word(0x0C, 0x9000)
        m.run('PRE_START', watch=[0x9000])
        self.assertEqual(s.word(0x0C), m['START'])
        self.assertEqual(s.word(m['DOSIN']), 0x9000)
        self.assertEqual(m.hits.get(0x9000), 1)
        m.run('START', watch=[0x9000])                # RESET: OS calls DOSINI
        self.assertEqual(m.hits.get(0x9000), 2, "DOS reset handler not chained")
        self.assertIn('EDOS 2.8', m.screen)

    def test_rerun_keeps_original_dosini(self):
        m = Machine()
        s = m.sim
        s.poke(0x9000, RTS)
        s.poke_word(0x0C, 0x9000)
        m.run('PRE_START')
        m.run('PRE_START')                            # EDOS run again
        self.assertEqual(s.word(m['DOSIN']), 0x9000)

    def test_escape_returns_to_menu_with_clean_stack(self):
        m = Machine(files(), lines=['TEXT.TXT'])      # no key: Esc at "Are You Sure?"
        m.run('COMERA')
        self.assertIsNotNone(m.file(1, 'TEXT.TXT'))
        m.sim.mpu.step()                              # GETCOM: LDX STKPTR
        m.sim.mpu.step()                              # TXS
        self.assertEqual(m.sim.mpu.sp, 0xFD)


if __name__ == '__main__':
    unittest.main()
