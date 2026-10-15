#!/usr/bin/env python3
"""Tests for tools/mac65tok.py (MAC/65 tokenized SAVE format)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mac65tok as t  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = ['EDOS.M65', 'EDOSVARS.M65', 'MACROS.M65', 'SYSTEM.M65', 'UTILS.M65', 'CIOSTAT.M65']


class TestTokens(unittest.TestCase):
    def test_known_encodings(self):
        # byte sequences as written by MAC/65 (from its saved files)
        cases = {
            "RTN   =   $7B     ;RTN KEY": b'\x83RTN\x1e\x06\x7b\x3b;RTN KEY',
            "    LDA FILPOS+1": b'\x51\x86FILPOS\x12\x08\x01',
            "    STA (INDPTR),Y": b'\x50\x40\x86INDPTR\x37',
            "    LDA # >START": b'\x51\x3e\x35\x85START',
            "    ASL A": b'\x54\x3f',
            "CS.128 .BYTE \"Key Abort\",EOL": b'\x86CS.128\x0b\x41\x89Key Abort\x41\x3d\x83EOL',
            "     @FILLMEM  FILE,$28,$20": b'\x07\x89@FILLMEM \x84FILE\x3d\x06\x28\x3d\x06\x20',
            "      .IF %0>3": b'\x01\x0c\x08\x00\x1c\x08\x03',
            "VDSLST = $0200": b'\x86VDSLST\x1e\x05\x00\x02',
            "    .INCLUDE #D:MACROS.M65": b'\x11\x3e\x8cD:MACROS.M65',
            "    .MACRO @CPYMEM": b'\x04\x88@CPYMEM ',
            "*=RUNAD": b'\x58*=RUNAD',
            "; COMMENT": b'\x58; COMMENT',
            "START_PROG": b'\x8aSTART_PROG',
        }
        for text, want in cases.items():
            self.assertEqual(t.tokenize_line(text), want, text)

    def test_repository_sources_round_trip(self):
        for name in SOURCES:
            with open(os.path.join(ROOT, name), encoding='utf-8') as f:
                tok = t.tokenize(f.read())
            self.assertEqual(tok[:2], b'\xfe\xfe')
            self.assertEqual(tok[2] | tok[3] << 8, len(tok) - 4)
            self.assertEqual(t.tokenize(t.detokenize(tok)), tok, name)

    def test_line_numbers_ascend(self):
        # MAC/65 keeps one line per number, in order: a repeated or
        # lower number would replace or reorder lines when loaded
        import re
        for name in SOURCES:
            with open(os.path.join(ROOT, name), encoding='utf-8') as f:
                nums = [int(re.match(r'(\d+)', l).group(1)) for l in f if l.strip()]
            bad = [(a, b) for a, b in zip(nums, nums[1:]) if b <= a]
            self.assertEqual(bad, [], name)

    def test_rejects_unknown(self):
        with self.assertRaises(t.TokError):
            t.tokenize_line("    FOO BAR")


if __name__ == '__main__':
    unittest.main()
