#!/usr/bin/env python3
"""Tests for the disks made by tools/make_disks.py."""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'xl', 'tools'))
import sparta  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, 'build')
ORIGINAL = os.path.join(ROOT, 'tools', 'disk', 'BASE.ATR')


def content(d, name):
    e = d.find(name)[1]
    return d.read_file(d.w(e, 1), e[3] | e[4] << 8 | e[5] << 16)


class TestBaseImage(unittest.TestCase):
    def test_base_is_clean_and_bootable(self):
        d = sparta.Disk(ORIGINAL)
        self.assertEqual(d.fsck(), ([], []))
        self.assertTrue(content(d, 'X32G.DOS').startswith(b'\xff\xff'))
        self.assertEqual(d.w(d.read(1), 0x28), d.w(d.find('X32G.DOS')[1], 1))


@unittest.skipUnless(os.path.exists(os.path.join(BUILD, 'EDOSTEST.ATR')), 'run make_disks.py')
class TestBuiltDisks(unittest.TestCase):
    def test_disks_are_clean_and_bootable(self):
        edos = sparta._read(os.path.join(BUILD, 'EDOS.COM'))
        for name in ('EDOS.ATR', 'EDOSTEST.ATR'):
            d = sparta.Disk(os.path.join(BUILD, name))
            self.assertEqual(d.fsck(), ([], []), name)
            self.assertEqual(content(d, 'EDOS.COM'), edos, name)
            dos = d.find('X32G.DOS')[1]
            self.assertEqual(d.w(d.read(1), 0x28), d.w(dos, 1), f"{name}: boot file pointer")
            self.assertEqual(content(d, 'X32G.DOS'), content(sparta.Disk(ORIGINAL), 'X32G.DOS'))

    def test_other_files_carried_over(self):
        import make_disks
        old, new = sparta.Disk(ORIGINAL), sparta.Disk(os.path.join(BUILD, 'EDOS.ATR'))
        for i, e in old.entries():
            n = old.name(e)
            if old.live(e):
                self.assertEqual(content(new, n), content(old, n), n)

    def test_sources_on_disk_assemble_to_edos_com(self):
        import make_disks
        import mac65tok
        import subprocess
        from atari_src import numbered
        d = sparta.Disk(os.path.join(BUILD, 'EDOS.ATR'))
        with tempfile.TemporaryDirectory() as tmp:
            for n in make_disks.SOURCES:
                with open(os.path.join(ROOT, n), encoding='utf-8') as f:
                    self.assertEqual(content(d, n), mac65tok.tokenize(numbered(f.read())), n)
                with open(os.path.join(tmp, n), 'w', encoding='utf-8') as f:
                    f.write(mac65tok.detokenize(content(d, n)))
            out = os.path.join(tmp, 'EDOS.COM')
            subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'xl', 'tools', 'mac65.py'),
                            os.path.join(tmp, 'EDOS.M65'), '-o', out], check=True,
                           capture_output=True)
            self.assertEqual(sparta._read(out), sparta._read(os.path.join(BUILD, 'EDOS.COM')))


if __name__ == '__main__':
    unittest.main()
