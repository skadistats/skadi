import unittest
import io
import os

from skadi.index import epilogue as ndx_plg
from skadi.io.util import Peek
from protobuf.impl import demo_pb2 as pb_d


class TestEpilogue(unittest.TestCase):
    @classmethod
    def fabricate_entries(cls):
        return ((Peek(False, pb_d.DEM_FileInfo, 0, 0), ''),)

    @classmethod
    def mk(cls):
        entries = TestEpilogue.fabricate_entries()
        return ndx_plg.EpilogueIndex(entries)


if __name__ == '__main__':
    unittest.main()
