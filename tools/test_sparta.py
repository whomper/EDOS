#!/usr/bin/env python3
"""Tests for tools/sparta.py and the disks made by tools/make_disks.py."""
import os
import random
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sparta  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, 'build')
ORIGINAL = os.path.join(ROOT, 'EDOS.atr')


def content(d, name):
    e = d.find(name)[1]
    return d.read_file(d.w(e, 1), e[3] | e[4] << 8 | e[5] << 16)


class TestFileSystem(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, 'T.ATR')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_new_disk_is_clean(self):
        d = sparta.new_disk(self.path, ORIGINAL, 'T')
        self.assertEqual(d.fsck(), ([], []))
        self.assertEqual(d.total, 720)

    def test_add_remove_grow_roundtrip(self):
        rnd = random.Random(1)
        d = sparta.new_disk(self.path, ORIGINAL, 'T')
        files = {f'F{i}.DAT': bytes(rnd.randrange(256) for _ in range(rnd.randrange(1, 3000)))
                 for i in range(30)}                       # > 1 directory sector
        files['LARGE.DAT'] = bytes(rnd.randrange(256) for _ in range(40000))   # 2 sector maps
        for n, v in files.items():
            d.add(n, v)
        d.remove('F7.DAT')
        del files['F7.DAT']
        d.add('F3.DAT', b'replaced')
        files['F3.DAT'] = b'replaced'
        d.save()
        d = sparta.Disk(self.path)
        self.assertEqual(d.fsck(), ([], []))
        for n, v in files.items():
            self.assertEqual(content(d, n), v, n)
        self.assertIsNone(d.find('F7.DAT'))

    def test_disk_full(self):
        d = sparta.new_disk(self.path, ORIGINAL, 'T')
        with self.assertRaises(sparta.SpartaError):
            d.add('HUGE.DAT', bytes(200000))
        self.assertEqual(d.fsck(), ([], []))


class TestOriginalImage(unittest.TestCase):
    def test_reads_files(self):
        d = sparta.Disk(ORIGINAL)
        self.assertTrue(content(d, 'X32G.DOS').startswith(b'\xff\xff'))

    def test_known_damage_is_detected(self):
        problems, _ = sparta.Disk(ORIGINAL).fsck()
        if not problems:
            self.skipTest('EDOS.atr has been replaced by a clean image')
        self.assertTrue(any('sector 496' in p for p in problems))


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

    def test_original_files_carried_over(self):
        old, new = sparta.Disk(ORIGINAL), sparta.Disk(os.path.join(BUILD, 'EDOS.ATR'))
        for i, e in old.entries():
            n = old.name(e)
            if old.live(e) and n not in ('EDOS.COM', 'STARTUP.BAT', 'EDOS.DOC'):
                self.assertEqual(content(new, n), content(old, n), n)


if __name__ == '__main__':
    unittest.main()
