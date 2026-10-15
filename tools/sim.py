"""Minimal Atari XL simulation for unit-testing EDOS routines with py65.

Loads build/EDOS.COM and build/EDOS.SYM, gives the CPU a 64K main RAM plus
16 extended 16K banks selected through PORTB (bit 4 = CPU bank enable,
bits 2,3,5,6 = bank number, matching the BANKS table), and traps the OS
entry points EDOS calls so tests can stand in for CIO, SIO and the
floating-point ROM.

    sim = Sim()
    sim.call('CALCLEN')                  # JSR to a symbol, returns on RTS
    sim.sio_handler = lambda s: ...      # called on JSR SIOV / DSKINV
"""
import os

from py65.devices.mpu6502 import MPU

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.environ.get('EDOS_BUILD', os.path.join(ROOT, 'build'))

PORTB = 0xD301
SIOV, DSKINV, CIOV = 0xE459, 0xE453, 0xE456
AFP, FASC, IFP, FPI = 0xD800, 0xD8E6, 0xD9AA, 0xD9D2
FR0, LBUFF, INBUFF, CIX = 0xD4, 0x0580, 0xF3, 0xF2
DCB = 0x0300            # DDEVIC.. DAUX2
RETURN_TRAP = 0xFFF0    # fake return address that ends call()


class BankedMemory:
    # PORTB bits that select a bank: $6C = bits 2,3,5,6 -> 16 banks (256K);
    # $6E adds bit 1 -> 32 banks (512K)
    def __init__(self, bank_bits=0x6C):
        self.bank_bits = bank_bits
        self.main = bytearray(0x10000)
        self.banks = {}
        self.main[PORTB] = 0xFF

    def _bank(self, addr):
        pb = self.main[PORTB]
        if 0x4000 <= addr < 0x8000 and not pb & 0x10:
            key = pb & self.bank_bits
            return self.banks.setdefault(key, bytearray(0x4000))
        return None

    def __getitem__(self, addr):
        if isinstance(addr, slice):
            return [self[a] for a in range(*addr.indices(0x10000))]
        b = self._bank(addr)
        return b[addr - 0x4000] if b is not None else self.main[addr]

    def __setitem__(self, addr, val):
        if isinstance(addr, slice):
            for a, v in zip(range(*addr.indices(0x10000)), val):
                self[a] = v
            return
        b = self._bank(addr)
        if b is not None:
            b[addr - 0x4000] = val & 0xFF
        else:
            self.main[addr] = val & 0xFF

    def __len__(self):
        return 0x10000


def load_symbols(path=os.path.join(BUILD, 'EDOS.SYM')):
    syms = {}
    with open(path) as f:
        for line in f:
            name, val = line.split()
            syms[name] = int(val[1:], 16)
    return syms


def load_binary(mem, path=os.path.join(BUILD, 'EDOS.COM')):
    with open(path, 'rb') as f:
        d = f.read()
    i = 0
    while i < len(d):
        if d[i:i + 2] == b'\xff\xff':
            i += 2
        s = d[i] | d[i + 1] << 8
        e = d[i + 2] | d[i + 3] << 8
        i += 4
        for k in range(e - s + 1):
            mem.main[s + k] = d[i + k]
        i += e - s + 1


class Sim:
    def __init__(self, build=None, bank_bits=0x6C):
        self.mem = BankedMemory(bank_bits)
        build = build or BUILD
        load_binary(self.mem, os.path.join(build, 'EDOS.COM'))
        self.sym = load_symbols(os.path.join(build, 'EDOS.SYM'))
        self.mpu = MPU(memory=self.mem)
        self.sio_log = []
        self.cio_log = []
        self.sio_handler = None      # f(sim) -> status (Y); default 1
        self.cio_handler = None      # f(sim, iocb) -> status (Y); default 1
        self._fp = 0

    # -- memory helpers
    def __getitem__(self, name):
        return self.sym[name]

    def peek(self, addr):
        return self.mem[addr]

    def poke(self, addr, *vals):
        for k, v in enumerate(vals):
            self.mem[addr + k] = v

    def word(self, addr):
        return self.mem[addr] | self.mem[addr + 1] << 8

    def poke_word(self, addr, v):
        self.poke(addr, v & 0xFF, v >> 8)

    def dcb(self):
        m = self.mem
        return dict(dev=m[DCB], unit=m[DCB + 1], cmd=m[DCB + 2], stat=m[DCB + 3],
                    buf=m[DCB + 4] | m[DCB + 5] << 8, size=m[DCB + 8] | m[DCB + 9] << 8,
                    sector=m[DCB + 10] | m[DCB + 11] << 8, portb=m[PORTB])

    # -- execution
    def _rts(self, y=None, a=None):
        mpu = self.mpu
        lo = self.mem[0x100 + ((mpu.sp + 1) & 0xFF)]
        hi = self.mem[0x100 + ((mpu.sp + 2) & 0xFF)]
        mpu.sp = (mpu.sp + 2) & 0xFF
        mpu.pc = ((hi << 8) | lo) + 1
        if a is not None:
            mpu.a = a & 0xFF
        if y is not None:
            mpu.y = y & 0xFF
            mpu.p &= ~(mpu.NEGATIVE | mpu.ZERO)
            if y & 0x80:
                mpu.p |= mpu.NEGATIVE
            if y == 0:
                mpu.p |= mpu.ZERO

    def _trap(self):
        pc = self.mpu.pc
        if pc in (SIOV, DSKINV):
            st = self.dcb()
            self.sio_log.append(st)
            y = self.sio_handler(self) if self.sio_handler else 1
            self.mem[DCB + 3] = y
            self._rts(y=y)
        elif pc == CIOV:
            x = self.mpu.x
            self.cio_log.append(dict(iocb=x, cmd=self.mem[0x342 + x]))
            r = self.cio_handler(self, x) if self.cio_handler else 1
            y, a = r if isinstance(r, tuple) else (r, None)
            self._rts(y=y, a=a)
        elif pc == IFP:
            self._fp = self.mem[FR0] | self.mem[FR0 + 1] << 8
            self._rts()
        elif pc == FASC:
            s = str(self._fp).encode()
            for k, c in enumerate(s):
                self.mem[LBUFF + k] = c | (0x80 if k == len(s) - 1 else 0)
            self.poke_word(INBUFF, LBUFF)
            self._rts()
        elif pc == AFP:
            p = self.word(INBUFF) + self.mem[CIX]
            s = ''
            while chr(self.mem[p]).isdigit():
                s += chr(self.mem[p]); p += 1
            self._fp = int(s or '0')
            self._rts()
        elif pc == FPI:
            self.poke_word(FR0, self._fp)
            self._rts()
        else:
            return False
        return True

    def call(self, target, a=0, x=0, y=0, max_steps=5_000_000):
        """JSR to a symbol or address; run until it returns."""
        addr = self.sym[target] if isinstance(target, str) else target
        mpu = self.mpu
        mpu.sp = 0xFD
        ret = RETURN_TRAP - 1
        self.mem[0x1FF] = ret >> 8
        self.mem[0x1FE] = ret & 0xFF
        mpu.sp = 0xFD
        mpu.a, mpu.x, mpu.y, mpu.pc = a, x, y, addr
        for _ in range(max_steps):
            if mpu.pc == RETURN_TRAP:
                return mpu
            if mpu.pc >= 0xD800 and self._trap():
                continue
            mpu.step()
        raise RuntimeError(f"{target} did not return within {max_steps} steps (pc=${mpu.pc:04X})")
