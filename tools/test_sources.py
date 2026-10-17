#!/usr/bin/env python3
"""Tests for EDOS's MAC/65 sources: in git's form (no line numbers), and
as the tokenised files on the disk (xl/tools/atari_src.py, mac65tok.py)."""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'xl', 'tools'))
import mac65tok as t  # noqa: E402
import atari_src  # noqa: E402

ROOT = os.path.dirname(HERE)


def text(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return f.read()


def sources():
    """EDOS.M65 and EDOS's files it includes, in its order (not xl/'s AX files)"""
    names = re.findall(r'^ *\.INCLUDE #D:([A-Z0-9]+\.M65)', text('EDOS.M65'), re.M)
    return ['EDOS.M65'] + [n for n in names if not n.startswith('AX')]


SOURCES = sources()


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

    def test_headers_and_sizes(self):
        # each file starts "; NAME.M65 - EDOS x.y" with the version in
        # TTL2, and is at most 16K tokenised (atari_src.py disk checks both)
        import subprocess
        version = subprocess.run([sys.executable, os.path.join(HERE, 'version.py'), '--source'],
                                 capture_output=True, text=True, check=True).stdout.strip()
        for name in SOURCES:
            atari_src.to_disk(text(name), name, 'EDOS', version)

    def test_main_file_is_a_short_driver(self):
        # On the Atari EDOS.M65 is LOADed and assembled with ASM ,,#D:EDOS.COM.
        # ASM #D:EDOS.M65 fails on SpartaDOS: MAC/65 1.01 rewinds the file for
        # pass 2 with POINT, forcing ICAX5 = 2 (a DOS 2 sector offset), which
        # SpartaDOS reads as a 24-bit position past the end of the file. The
        # source in memory shares RAM with the symbol table (MEM FULL when
        # the whole program was in EDOS.M65), so it holds only the includes.
        self.assertLessEqual(len(t.tokenize(atari_src.numbered(text('EDOS.M65')))), 2048)

    def test_includes_are_not_nested(self):
        # MAC/65 stops with NESTED INCLUDE when an included file includes
        for name in SOURCES[1:]:
            self.assertNotIn('.INCLUDE', text(name).upper(), name)


if __name__ == '__main__':
    unittest.main()
