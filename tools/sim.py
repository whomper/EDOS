"""EDOS on xl's a8sim (xl/tools/a8sim), for the tests: the 6502, 64K and
16 extended 16K banks selected through PORTB (bit 4 = CPU bank enable,
bits 2,3,5,6 = the bank, as in BANKS), the floating point traps; CIO and
SIO go to the test's handlers.

Sim keeps the calls EDOS's tests use:

    sim = Sim()
    sim.call('CALCLEN')                  # JSR to a symbol, returns on RTS
    sim.sio_handler = lambda s: ...      # called on JSR SIOV / DSKINV
    sim.cio_handler = lambda s, x: ...   # called on JSR CIOV: Y or (Y, A)

Memory starts as EDOS's tests expect it: all zero but EDOS.COM (loaded
without running its INIT) and MEMTOP $9C1F (40K, GRAPHICS 0), not the
OS set-up a8sim's Machine makes for whole programs.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'xl', 'tools'))
from a8sim import Machine, BankedMemory, SIO, install_fp  # noqa: E402

BUILD = os.environ.get('EDOS_BUILD', os.path.join(ROOT, 'build'))

PORTB = 0xD301
DCB = 0x0300            # DDEVIC.. DAUX2


class Sim:
    def __init__(self, build=None, bank_bits=0x6C):
        build = build or BUILD
        self.mem = BankedMemory(bank_bits)
        self.m = m = Machine(memory=self.mem, clock='steps')
        self.mem.main[:] = bytes(0x10000)                 # not Machine's OS set-up
        self.mem.main[PORTB] = 0xFF
        m.load(os.path.join(build, 'EDOS.COM'), init=False)
        self.poke_word(0x2E5, 0x9C1F)                     # MEMTOP: 40K, GRAPHICS 0
        self.sym = m.load_symbols(os.path.join(build, 'EDOS.SYM'))
        self.mpu = m.mpu
        m.unknown = 'run'          # other OS addresses run on, as before
        m.cio = _CIO(self)
        m.sio = SIO(fallback=self._sio)
        install_fp(m)
        self.sio_log = []
        self.cio_log = []
        self.sio_handler = None      # f(sim) -> status (Y); default 1
        self.cio_handler = None      # f(sim, iocb) -> status (Y) or (Y, A); default 1

    # -- the handlers, as a8sim calls them
    def _sio(self, m, dcb):
        self.sio_log.append(self.dcb())
        return self.sio_handler(self) if self.sio_handler else 1

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
    def _trap(self):
        """the OS call at PC, if a8sim stands in for it: True when done"""
        return self.m._trap(self.mpu.pc)

    def call(self, target, a=0, x=0, y=0, max_steps=5_000_000):
        """JSR to a symbol or address; run until it returns."""
        return self.m.call(target, a=a, x=x, y=y, max_steps=max_steps)


class _CIO:
    """a8sim's CIO: the test's cio_handler, (Y, A) for IOCB X"""

    def __init__(self, sim):
        self.sim = sim

    def call(self, m, x):
        s = self.sim
        s.cio_log.append(dict(iocb=x, cmd=s.mem[0x342 + x]))
        r = s.cio_handler(s, x) if s.cio_handler else 1
        return r if isinstance(r, tuple) else (r, None)
