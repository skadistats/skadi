
import unittest
import io
import os

from skadi.index.embed import dem_signon_packet
from skadi.io.util import Peek
from protobuf.impl import netmessages_pb2 as pb_n


class TestDemSignonPacket(unittest.TestCase):
    @classmethod
    def fabricate_entries(cls):
        entries = (
            (Peek(False, pb_n.svc_GameEventList, 0, 0), ''),
            (Peek(False, pb_n.svc_ServerInfo, 0, 0), ''),
            (Peek(False, pb_n.svc_VoiceInit, 0, 0), ''),
            (Peek(False, pb_n.svc_CreateStringTable, 0, 0), ''),
            (Peek(False, pb_n.svc_CreateStringTable, 0, 0), ''),
            (Peek(False, pb_n.svc_CreateStringTable, 0, 0), ''),
            (Peek(False, pb_n.svc_CreateStringTable, 0, 0), ''),
            (Peek(False, pb_n.svc_CreateStringTable, 0, 0), '')
        )

        return entries

    @classmethod
    def mk(cls):
        entries = TestDemSignonPacket.fabricate_entries()
        return dem_signon_packet.mk(entries)

    def test_svc_game_event_list_returns_match(self):
        index = TestDemSignonPacket.mk()
        peek, message = index.svc_game_event_list
        self.assertEqual(pb_n.svc_GameEventList, peek.kind)

    def test_svc_server_info_returns_match(self):
        index = TestDemSignonPacket.mk()
        peek, message = index.svc_server_info
        self.assertEqual(pb_n.svc_ServerInfo, peek.kind)

    def test_svc_voice_init_returns_match(self):
        index = TestDemSignonPacket.mk()
        peek, message = index.svc_voice_init
        self.assertEqual(pb_n.svc_VoiceInit, peek.kind)

    def test_all_svc_create_string_table_returns_match(self):
        index = TestDemSignonPacket.mk()
        entries = list(index.all_svc_create_string_table)
        self.assertEqual(5, len(entries))
        for peek, message in entries:
            self.assertEqual(pb_n.svc_CreateStringTable, peek.kind)


if __name__ == '__main__':
    unittest.main()
