import unittest
import io
import os

from skadi.index import generic as ind_generic
from skadi.io.util import Peek

class TestGeneric(unittest.TestCase):
    @classmethod
    def fabricate_entries(cls, count):
        kinds = (1, 2, 3)

        entries = []

        for i in range(count):
            comp = bool(i % 2)
            kind = kinds[i % 3]
            tick = i
            size = 3
            peek = Peek(comp, kind, tick, size)
            entries.append((peek, '\1\2\3'))

        return entries

    @classmethod
    def mk(cls, entries):
        return ind_generic.mk(entries)

    def test_find_kind_returns_one_entry(self):
        entries = TestGeneric.fabricate_entries(30)
        index = TestGeneric.mk(entries)
        peek, message = index.find_kind(1)
        self.assertFalse(peek.compressed)
        self.assertEqual(1, peek.kind)
        self.assertEqual(0, peek.tick)
        self.assertEqual(3, peek.size)

    def test_find_all_kind_returns_matching_entries(self):
        entries = TestGeneric.fabricate_entries(30)
        index = TestGeneric.mk(entries)
        found = index.find_all_kind(1)
        self.assertEqual(10, len(list(found)))
        for peek, message in found:
            self.assertEqual(1, peek.kind)

if __name__ == '__main__':
    unittest.main()
