import unittest
import io
import os

from skadi.index import prologue
from skadi.io import demo as io_dm
from skadi.io.util import Peek
from protobuf.impl import demo_pb2 as pb_d


class TestPrologue(unittest.TestCase):
    @classmethod
    def fabricate_entries(cls):
        entries = (
            (Peek(False, pb_d.DEM_FileHeader, 0, 0), ''),
            (Peek(False, pb_d.DEM_ClassInfo, 0, 0), ''),
            (Peek(False, pb_d.DEM_SendTables, 0, 0), ''),
            (Peek(False, pb_d.DEM_SignonPacket, 0, 0), ''),
            (Peek(False, pb_d.DEM_SignonPacket, 0, 0), ''),
            (Peek(False, pb_d.DEM_SignonPacket, 0, 0), ''),
            (Peek(False, pb_d.DEM_SignonPacket, 0, 0), ''),
            (Peek(False, pb_d.DEM_SignonPacket, 0, 0), '')
        )

        return entries

    @classmethod
    def mk(cls):
        entries = TestPrologue.fabricate_entries()
        return prologue.PrologueIndex(entries)

    def test_dem_file_header_returns_match(self):
        index = TestPrologue.mk()
        peek, message = index._dem_file_header
        self.assertEqual(pb_d.DEM_FileHeader, peek.kind)

    def test_dem_class_info(self):
        index = TestPrologue.mk()
        peek, message = index._dem_class_info
        self.assertEqual(pb_d.DEM_ClassInfo, peek.kind)

    def test_dem_send_tables(self):
        index = TestPrologue.mk()
        peek, message = index._dem_send_tables
        self.assertEqual(pb_d.DEM_SendTables, peek.kind)

    def test_all_dem_signon_packet(self):
        index = TestPrologue.mk()
        entries = list(index._all_dem_signon_packet)
        self.assertEqual(5, len(entries))
        for peek, message in entries:
            self.assertEqual(pb_d.DEM_SignonPacket, peek.kind)


if __name__ == '__main__':
    unittest.main()
