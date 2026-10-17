#!/usr/bin/env python3
"""Tests for EDOS's MAC/65 sources: in git's form (no line numbers), and
as the tokenised files on the disk (xl/tools/atari_src.py, mac65tok.py)."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'xl', 'tools'))
import mac65tok as t  # noqa: E402
import atari_src  # noqa: E402

ROOT = os.path.dirname(HERE)
SOURCES = ['EDOS.M65', 'EDOSMAIN.M65', 'EDOSVARS.M65', 'MACROS.M65', 'SYSTEM.M65', 'UTILS.M65', 'CIOSTAT.M65']


def text(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return f.read()


class TestSources(unittest.TestCase):
    def test_round_trip(self):
        for name in SOURCES:
            tok = t.tokenize(atari_src.numbered(text(name)))
            self.assertEqual(tok[:2], b'\xfe\xfe')
            self.assertEqual(tok[2] | tok[3] << 8, len(tok) - 4)
            self.assertEqual(t.tokenize(t.detokenize(tok)), tok, name)

    def test_no_line_numbers_in_git(self):
        # git keeps the sources without numbers; the disk gets 10, 20, ...
        for name in SOURCES:
            atari_src.numbered(text(name))   # raises on a numbered line

    def test_main_file_is_a_short_driver(self):
        # On the Atari EDOS.M65 is LOADed and assembled with ASM ,,#D:EDOS.COM.
        # ASM #D:EDOS.M65 fails on SpartaDOS: MAC/65 1.01 rewinds the file for
        # pass 2 with POINT, forcing ICAX5 = 2 (a DOS 2 sector offset), which
        # SpartaDOS reads as a 24-bit position past the end of the file. The
        # source in memory shares RAM with the symbol table (MEM FULL when
        # the whole program was in EDOS.M65), so it holds only the includes.
        self.assertLess(len(t.tokenize(atari_src.numbered(text('EDOS.M65')))), 1024)

    def test_includes_are_not_nested(self):
        # MAC/65 stops with NESTED INCLUDE when an included file includes
        for name in SOURCES[1:]:
            self.assertNotIn('.INCLUDE', text(name).upper(), name)


if __name__ == '__main__':
    unittest.main()
