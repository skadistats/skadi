cimport skadi_ext.index.generic
import importlib as il
import os

from protobuf.impl import netmessages_pb2 as pb_n


cpdef mk(object entries):
    return DemPacketIndex(entries)


cdef class DemPacketIndex(skadi_ext.index.generic.Index):
    def __init__(DemPacketIndex self, object entries):
        super(DemPacketIndex, self).__init__(entries)

    property net_tick:
        def __get__(self):
            return self.find_kind(pb_n.net_Tick)

    property svc_packet_entities:
        def __get__(self):
            return self.find_kind(pb_n.svc_PacketEntities)

    property all_svc_update_string_table:
        def __get__(self):
            return self.find_all_kind(pb_n.svc_UpdateStringTable)

    property all_svc_game_event:
        def __get__(self):
            return self.find_all_kind(pb_n.svc_GameEvent)

    property all_svc_user_message:
        def __get__(self):
            return self.find_all_kind(pb_n.svc_UserMessage)
