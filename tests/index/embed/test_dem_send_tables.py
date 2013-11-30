import unittest
import io
import os

from skadi.index.embed import dem_send_tables
from skadi.io.util import Peek
from protobuf.impl import netmessages_pb2 as pb_n


class TestDemSendTables(unittest.TestCase):
    @classmethod
    def fabricate_entries(cls):
        entries = (
            (Peek(False, pb_n.svc_SendTable, 0, 0), ''),
            (Peek(False, pb_n.svc_SendTable, 0, 0), ''),
            (Peek(False, pb_n.svc_SendTable, 0, 0), ''),
            (Peek(False, pb_n.svc_SendTable, 0, 0), ''),
            (Peek(False, pb_n.svc_SendTable, 0, 0), '')
        )

        return entries

    @classmethod
    def mk(cls):
        entries = TestDemSendTables.fabricate_entries()
        return dem_send_tables.mk(entries)

    def test_all_svc_send_table(self):
        index = TestDemSendTables.mk()
        entries = list(index.all_svc_send_table)
        self.assertEqual(5, len(entries))
        for peek, message in entries:
            self.assertEqual(pb_n.svc_SendTable, peek.kind)


if __name__ == '__main__':
    unittest.main()
