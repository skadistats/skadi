import importlib as il
import io
import os
import unittest

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
ndx_mbd_dmpckt = il.import_module(__impl__ + '.index.embed.dem_packet')

from skadi.io.util import Peek
from protobuf.impl import netmessages_pb2 as pb_n


class TestDemPacket(unittest.TestCase):
    @classmethod
    def fabricate_entries(cls):
        entries = (
            (Peek(False, pb_n.net_Tick, 0, 0), ''),
            (Peek(False, pb_n.svc_PacketEntities, 0, 0), ''),
            (Peek(False, pb_n.svc_UpdateStringTable, 0, 0), ''),
            (Peek(False, pb_n.svc_UpdateStringTable, 0, 0), ''),
            (Peek(False, pb_n.svc_UpdateStringTable, 0, 0), ''),
            (Peek(False, pb_n.svc_GameEvent, 0, 0), ''),
            (Peek(False, pb_n.svc_GameEvent, 0, 0), ''),
            (Peek(False, pb_n.svc_GameEvent, 0, 0), ''),
            (Peek(False, pb_n.svc_UserMessage, 0, 0), ''),
            (Peek(False, pb_n.svc_UserMessage, 0, 0), ''),
            (Peek(False, pb_n.svc_UserMessage, 0, 0), '')
        )

        return entries

    @classmethod
    def mk(cls):
        entries = TestDemPacket.fabricate_entries()
        return ndx_mbd_dmpckt.mk(entries)

    def test_net_tick(self):
        index = TestDemPacket.mk()
        peek, message = index.net_tick
        self.assertEqual(pb_n.net_Tick, peek.kind)

    def test_svc_packet_entities(self):
        index = TestDemPacket.mk()
        peek, message = index.svc_packet_entities
        self.assertEqual(pb_n.svc_PacketEntities, peek.kind)

    def test_all_svc_update_string_table(self):
        index = TestDemPacket.mk()
        entries = list(index.all_svc_update_string_table)
        self.assertEqual(3, len(entries))
        for peek, message in entries:
            self.assertEqual(pb_n.svc_UpdateStringTable, peek.kind)

    def test_all_svc_game_event(self):
        index = TestDemPacket.mk()
        entries = list(index.all_svc_game_event)
        self.assertEqual(3, len(entries))
        for peek, message in entries:
            self.assertEqual(pb_n.svc_GameEvent, peek.kind)

    def test_all_svc_user_message(self):
        index = TestDemPacket.mk()
        entries = list(index.all_svc_user_message)
        self.assertEqual(3, len(entries))
        for peek, message in entries:
            self.assertEqual(pb_n.svc_UserMessage, peek.kind)


if __name__ == '__main__':
    unittest.main()
