#!/usr/bin/env python3
"""Differential test: run EDOS commands on two builds and compare behaviour.

    tools/difftest.py OLD_BUILD_DIR NEW_BUILD_DIR [scenario ...]

Each scenario starts one menu command with scripted keys/lines, a fake DOS
(files on D1:/D2:, directory listings, rename/erase/protect, EOF and error
statuses) and a fake disk drive, and runs until the command returns to
GETCOM. For both builds it records:

  * everything printed to the screen
  * every CIO call (IOCB, command, buffer, length, aux) and SIO call
    (command, unit, sector, buffer, size), with addresses inside EDOS
    translated to symbol+offset so that moved code still compares equal
  * the files left on the fake disks and selected memory ranges

and reports any difference. Size optimisations must not change any of it.
"""
import fnmatch
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import Sim, DCB  # noqa: E402

EOL = 0x9B
IOCB = 0x340


class Done(Exception):
    pass


def atascii(s):
    return bytes(ord(c) for c in s)


class World:
    """Fake DOS + keyboard + editor + disk drive behind CIOV/SIOV."""

    def __init__(self, sim, files, keys, lines, symbolize):
        self.sim = sim
        self.files = {d: {n: [bytearray(v), False] for n, v in fs.items()} for d, fs in files.items()}
        self.keys = list(keys)
        self.dfile = set()                               # IOCBs >0 with a D: file open
        self.lines = list(lines)
        self.sym = symbolize
        self.open = {}
        self.screen = bytearray()
        self.trace = []
        self.disk = {}
        self.ignore_len = False
        self.dvstat = 0                                  # drive status byte 0

    # ---------------------------------------------------------------- CIO
    def field(self, x, off, n=1):
        m = self.sim.mem
        return m[IOCB + x + off] if n == 1 else m[IOCB + x + off] | m[IOCB + x + off + 1] << 8

    def set_len(self, x, n):
        self.sim.poke(IOCB + x + 8, n & 0xFF, n >> 8)

    def text_at(self, addr, limit=64):
        out = ''
        for k in range(limit):
            c = self.sim.peek(addr + k)
            if c == EOL:
                break
            out += chr(c & 0x7F)
        return out

    def parse_spec(self, spec):
        spec = spec.strip().upper().replace(' ', '')
        drive = 1
        if len(spec) > 2 and spec[0] == 'D' and spec[1].isdigit() and spec[2] == ':':
            drive, spec = int(spec[1]), spec[3:]
        elif spec.startswith('D:'):
            spec = spec[2:]
        return drive, spec

    def matches(self, drive, pat):
        pat = pat or '*.*'
        names = sorted(self.files.setdefault(drive, {}))
        return [n for n in names if fnmatch.fnmatch(n, pat) or (pat == '*.*')]

    def cio(self, sim, x):
        cmd = self.field(x, 2)
        buf = self.field(x, 4, 2)
        blen = self.field(x, 8, 2)
        ax1 = self.field(x, 10)
        rec = dict(iocb=x, cmd=cmd, buf=self.sym(buf), len=blen, ax1=ax1, ax2=self.field(x, 11))
        if cmd == 3:
            rec['name'] = self.text_at(buf)
        if self.ignore_len:
            del rec['len']
        self.trace.append(('CIO', tuple(sorted(rec.items()))))
        if x == 0:
            return self.editor(cmd, buf, blen)
        if x == 0x10 and cmd == 3 and not self.text_at(buf).startswith('K'):
            self.dfile.add(x)                            # a file on IOCB #1 (Load Binary)
        if x == 0x10 and x not in self.dfile:
            if cmd == 7 and blen == 0:
                if not self.keys:
                    return (1, 0x1B)                     # Esc: abort to menu
                return (1, ord(self.keys.pop(0)))
            return 1
        if cmd == 12:
            self.dfile.discard(x)
        return self.dos(x, cmd, buf, blen, ax1)

    def editor(self, cmd, buf, blen):
        if cmd in (0x0B, 0x09):
            self.screen += bytes(self.sim.peek(buf + k) for k in range(blen))
            return 1
        if cmd == 5:
            if not self.lines:
                raise Done("ran out of scripted input lines")
            data = atascii(self.lines.pop(0)) + bytes([EOL])
            n = min(len(data), blen)
            for k in range(n):
                self.sim.poke(buf + k, data[k])
            self.set_len(0, n)
            return 1 if n == len(data) else 137
        return 1

    def dos(self, x, cmd, buf, blen, ax1):
        if cmd == 3:                                     # OPEN
            drive, name = self.parse_spec(self.text_at(buf))
            if ax1 == 6:
                lines = b''
                for n in self.matches(drive, name):
                    data, lock = self.files[drive][n]
                    base, _, ext = n.partition('.')
                    secs = (len(data) + 124) // 125
                    lines += atascii(f"{'*' if lock else ' '} {base:<8}{ext:<3} {secs:03d}") + bytes([EOL])
                lines += atascii("532 FREE SECTORS") + bytes([EOL])
                self.open[x] = dict(mode='r', data=bytearray(lines), pos=0)
                return 1
            if ax1 & 8:
                f = self.files.setdefault(drive, {}).get(name)
                if f and f[1]:
                    return 167
                self.open[x] = dict(mode='w', drive=drive, name=name, data=bytearray())
                return 1
            f = self.files.setdefault(drive, {}).get(name)
            if not f:
                return 170
            self.open[x] = dict(mode='r', data=f[0], pos=0)
            return 1
        if cmd == 0x0C:                                  # CLOSE
            h = self.open.pop(x, None)
            if h and h['mode'] == 'w':
                self.files[h['drive']][h['name']] = [h['data'], False]
            return 1
        if cmd == 7:                                     # GET BINARY
            h = self.open.get(x)
            if not h:
                return 133
            n = min(blen, len(h['data']) - h['pos'])
            for k in range(n):
                self.sim.mem[buf + k] = h['data'][h['pos'] + k]
            h['pos'] += n
            self.set_len(x, n)
            return 1 if n == blen else 136
        if cmd == 0x0B:                                  # PUT BINARY
            h = self.open.get(x)
            if not h:
                return 133
            if blen == 0:                                # CIO: length 0 puts the
                h['data'] += bytes([self.sim.mpu.a])     # byte in A
            h['data'] += bytes(self.sim.mem[buf + k] for k in range(blen))
            return 1
        spec = self.text_at(buf)
        if cmd == 0x20:                                  # RENAME D1:OLD,NEW
            old, _, new = spec.partition(',')
            drive, pat = self.parse_spec(old)
            hits = self.matches(drive, pat)
            if not hits:
                return 170
            for n in hits:
                self.files[drive][new.strip().upper()] = self.files[drive].pop(n)
            return 1
        if cmd in (0x21, 0x23, 0x24):                    # ERASE / PROTECT / UNPROTECT
            drive, pat = self.parse_spec(spec)
            hits = self.matches(drive, pat)
            if not hits:
                return 170
            for n in hits:
                if cmd == 0x21:
                    if self.files[drive][n][1]:
                        return 167
                    del self.files[drive][n]
                else:
                    self.files[drive][n][1] = cmd == 0x23
            return 1
        if cmd == 0xFE:                                  # FORMAT
            drive, _ = self.parse_spec(spec)
            self.files[drive] = {}
            return 1
        return 1

    # ---------------------------------------------------------------- SIO
    def sio(self, sim):
        st = sim.sio_log[-1]
        banked = not st['portb'] & 0x10 and 0x4000 <= st['buf'] < 0x8000
        self.trace.append(('SIO', st['cmd'], st['unit'], st['sector'],
                           f"${st['buf']:04X}" if banked else self.sym(st['buf']),
                           st['size'], st['portb']))
        cmd = st['cmd']
        if cmd == 0x53:
            sim.poke(0x02EA, self.dvstat, 0, 0, 0)       # $20 double, $80 enhanced
            return 1 if st['unit'] <= 2 else 138
        if cmd in (0x3F, 0x68):
            return 0x8B                                  # no fast-SIO drive
        if cmd == 0x52:
            for i in range(st['size']):
                sim.mem[st['buf'] + i] = (st['sector'] * 7 + i * 13) & 0xFF
            return 1
        if cmd == 0x57:
            self.disk[(st['unit'], st['sector'])] = bytes(sim.mem[st['buf'] + i] for i in range(st['size']))
            return 1
        return 1


def symbolizer(sim):
    lo, hi = sim['START_PROG'], sim.sym.get('VAREND', sim['END_PROG'])
    named = {}
    for k, v in sorted(sim.sym.items()):
        if '?' in k:
            continue
        if lo <= v <= hi or 0xB0 <= v <= 0xCF or k in ('BUF', 'FILE', 'INP1', 'M4000', 'M5000', 'FSIOV'):
            named.setdefault(v, k)
    keys = sorted(v for v in named if lo <= v <= hi)

    def sym(a):
        if a in named:
            return named[a]
        if lo <= a <= hi:
            import bisect
            i = bisect.bisect_right(keys, a) - 1
            return f"{named[keys[i]]}+{a - keys[i]}"
        return f"${a:04X}"
    return sym


def run(build, sc):
    sim = Sim(build)
    w = World(sim, sc.get('files', {}), sc.get('keys', ''), sc.get('lines', []), symbolizer(sim))
    w.ignore_len = sc.get('ignore_lengths', False)   # e.g. saving EDOS itself
    w.dvstat = sc.get('dvstat', 0)
    sim.cio_handler = w.cio
    sim.sio_handler = w.sio
    sim.poke(sim['DSKNUM'], 1)
    sim.poke(sim['NUMBKS'], sc.get('numbks', 16))
    if 'RTNPTR' in sim.sym:                         # 2.9 and earlier
        sim.poke_word(sim['RTNPTR'], sim['GETCOM'])
    sim.poke(sim['STKPTR'], 0xFD)
    for a, data in sc.get('mem', {}).items():
        sim.poke(a, *data)
    for name, val in sc.get('zp', {}).items():
        sim.poke(sim[name], val)
    mpu = sim.mpu
    mpu.sp, mpu.a = 0xFD, sc.get('a', 0)
    mpu.pc = sim[sc['entry']]
    if sc['entry'] in MENU_KEY:                      # through the dispatcher,
        mpu.pc, mpu.a = sim['FINDCM'], ord(MENU_KEY[sc['entry']])   # title bar included
    stop = sim['GETCOM']
    note = ''
    try:
        for step in range(20_000_000):
            if mpu.pc == stop and step:
                break
            if mpu.pc >= 0xD800 and sim._trap():
                continue
            mpu.step()
        else:
            note = 'did not return to GETCOM'
    except Done as e:
        note = str(e)
    for x in list(w.open):                     # GETCOM's CLOSEIO
        w.dos(x, 0x0C, 0, 0, 0)
    mem = {f"${a:04X}": bytes(sim.mem[a + k] for k in range(n)) for a, n in sc.get('check_mem', [])}
    files = {d: {n: (bytes(v[0]), v[1]) for n, v in fs.items()} for d, fs in w.files.items()}
    if sc.get('ignore_file_data'):
        files = {d: {n: v[1] for n, v in fs.items()} for d, fs in files.items()}
    return dict(screen=bytes(w.screen), trace=w.trace, files=files, mem=mem,
                disk=w.disk if not sc.get('ignore_disk') else len(w.disk), note=note)


def binfile(*segs, run=None, init=None):
    out = bytearray(b'\xff\xff')
    for start, data in segs:
        out += bytes([start & 0xFF, start >> 8, (start + len(data) - 1) & 0xFF, (start + len(data) - 1) >> 8])
        out += bytes(data)
        if init and start == init[0]:
            out += bytes([0xE2, 0x02, 0xE3, 0x02, init[1] & 0xFF, init[1] >> 8])
    if run:
        out += bytes([0xE0, 0x02, 0xE1, 0x02, run & 0xFF, run >> 8])
    return bytes(out)


PROG = binfile((0x5000, b'\xa9\x01\x60' + bytes(range(253))), (0x5200, b'\x60'),
               run=0x5000, init=(0x5200, 0x5200))
PROG2 = b'\xff\xff' + bytes([0x00, 0x53, 0x03, 0x53]) + b'ABCD' + b'\xff\xff' + \
        bytes([0x00, 0x54, 0xFF, 0x54]) + bytes(range(256))
BIG = bytes((i * 7) & 0xFF for i in range(20000))
BASE = {1: {'A.COM': PROG, 'A2.COM': PROG, 'B.TXT': b'hello world\x9b' * 40,
            'P2.COM': PROG2, 'BIG.DAT': BIG}}
PATTERN = [(0x5000, bytes((i * 5 + 3) & 0xFF for i in range(512)))]

MENU_KEY = {'COMDIR': 'F', 'COMCAR': 'T', 'COMCPY': 'C', 'COMDUP': 'D', 'COMERA': 'E',
            'COMINI': 'I', 'COMVIE': 'V', 'COMANA': 'A', 'COMPRC': 'P', 'COMUNP': 'U',
            'COMREN': 'R', 'COMSAV': 'S', 'COMLOA': 'L', 'COMGOT': 'G', 'COMNEW': 'N',
            'COMMEM': 'M', 'COMCMP': 'B', 'COMWRT': 'W'}

SCENARIOS = {
    'menu': dict(entry='GOMENU'),
    'dir': dict(entry='COMDIR', lines=[''], files=BASE),
    'dir_pattern': dict(entry='COMDIR', lines=['*.COM'], files=BASE),
    'dir_even': dict(entry='COMDIR', lines=['A*.COM'], files=BASE),
    'load_no_run': dict(entry='COMLOA', lines=['D1:A.COM'], keys='N', files=BASE,
                        check_mem=[(0x5000, 0x110), (0x5200, 1)]),
    'load_ffff_mid': dict(entry='COMLOA', lines=['P2.COM'], keys='N', files=BASE,
                          check_mem=[(0x5300, 4), (0x5400, 0x100)]),
    'load_not_binary': dict(entry='COMLOA', lines=['B.TXT'], keys='N', files=BASE),
    'load_missing': dict(entry='COMLOA', lines=['NOPE.COM'], keys='N', files=BASE),
    'save': dict(entry='COMSAV', lines=['D1:OUT.COM', '5000', '50FF', '5000'], files=BASE,
                 mem=dict(PATTERN)),
    'save_no_run': dict(entry='COMSAV', lines=['OUT2.COM', '5010', '5020', ''], files=BASE,
                        mem=dict(PATTERN)),
    'save_bad_range': dict(entry='COMSAV', lines=['OUT3.COM', '50FF', '5000', ''], files=BASE),
    'copy_to_d2': dict(entry='COMCPY', lines=['D1:*.*'], keys='2', files=BASE),
    'copy_same_drive': dict(entry='COMCPY', lines=['D1:B.TXT'], keys='YYY', files=BASE),
    'copy_no_xmem': dict(entry='COMCPY', lines=['D1:B.TXT'], keys='2', files=BASE, numbks=0),
    'compare_same': dict(entry='COMCMP', lines=['A.COM', 'A2.COM'], files=BASE),
    'compare_diff': dict(entry='COMCMP', lines=['A.COM', 'P2.COM'], files=BASE),
    'view': dict(entry='COMVIE', lines=['B.TXT', '0010'], keys='YN', files=BASE),
    'view_big_offset': dict(entry='COMVIE', lines=['BIG.DAT', '1234'], keys='N', files=BASE),
    'erase': dict(entry='COMERA', lines=['B.TXT'], keys='Y', files=BASE),
    'erase_no': dict(entry='COMERA', lines=['B.TXT'], keys='N', files=BASE),
    'rename': dict(entry='COMREN', lines=['A.COM', 'C.COM'], keys='Y', files=BASE),
    'protect': dict(entry='COMPRC', lines=['A*.COM'], files=BASE),
    'unprotect': dict(entry='COMUNP', lines=['A.COM'], files=BASE),
    'memory': dict(entry='COMMEM', lines=['5000'], keys='+-N', mem=dict(PATTERN)),
    'analyze': dict(entry='COMANA', lines=['10'], keys='+-N'),
    'analyze_double': dict(entry='COMANA', lines=['720'], keys='+-N', dvstat=0x20),
    'format_single': dict(entry='COMINI', keys='1Y', files=BASE),
    'format_enhanced': dict(entry='COMINI', keys='2Y'),
    'new_drive': dict(entry='COMNEW', keys='2'),
    'duplicate': dict(entry='COMDUP', keys='YY', zp={'DENSITY': 1}),
    'duplicate_enhanced': dict(entry='COMDUP', keys='YY', dvstat=0x80),
    'duplicate_double': dict(entry='COMDUP', keys='YY', dvstat=0x20),
    'duplicate_to_d2': dict(entry='COMDUP', keys='Y2', dvstat=0x80),
    'write_edos': dict(entry='COMWRT', keys='Y', ignore_file_data=True, ignore_lengths=True),
}


def compare(a, b):
    diffs = []
    for k in ('note', 'screen', 'files', 'mem', 'disk'):
        if a[k] != b[k]:
            diffs.append(k)
    if a['trace'] != b['trace']:
        for i, (x, y) in enumerate(zip(a['trace'], b['trace'])):
            if x != y:
                diffs.append(f"trace[{i}]: {x} != {y}")
                break
        else:
            diffs.append(f"trace length {len(a['trace'])} != {len(b['trace'])}")
    return diffs


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    old, new, names = sys.argv[1], sys.argv[2], sys.argv[3:] or list(SCENARIOS)
    bad = 0
    for name in names:
        a, b = run(old, SCENARIOS[name]), run(new, SCENARIOS[name])
        d = compare(a, b)
        status = 'same' if not d else 'DIFFERENT: ' + '; '.join(d)
        extra = f"  ({a['note']})" if a['note'] else ''
        print(f"{name:<18} {len(a['trace']):4d} calls  {status}{extra}")
        bad += bool(d)
    print(f"{len(names) - bad}/{len(names)} scenarios identical")
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
