import importlib as il
import os

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
ndx_gnrc = il.import_module(__impl__ + '.index.generic')

from protobuf.impl import netmessages_pb2 as pb_n


def mk(*args):
    """
    Pass-through for DemPacketIndex instantiation.

    """
    return DemPacketIndex(*args)


class DemPacketIndex(ndx_gnrc.Index):
    """
    Facilitates constant-time, expressive fetching of 'svc' messages embedded
    in a CDemoPacket (protobuf.impl.demo_pb2) 'data' field.

    """

    def __init__(self, entries):
        """
        Initialize instance of index.

        Argument:
        entries -- list of (peek, message) to index

        """
        super(DemPacketIndex, self).__init__(entries)

    @property
    def net_tick(self):
        """
        Returns (peek, message) for 'net tick.'

        """
        return self.find_kind(pb_n.net_Tick)

    @property
    def svc_packet_entities(self):
        """
        Returns (peek, message) for 'packet entities.'

        """
        return self.find_kind(pb_n.svc_PacketEntities)

    @property
    def all_svc_update_string_table(self):
        """
        Returns list of (peek, message) for 'update string table.'

        """
        return self.find_all_kind(pb_n.svc_UpdateStringTable)

    @property
    def all_svc_game_event(self):
        """
        Returns list of (peek, message) for 'game event.'

        """
        return self.find_all_kind(pb_n.svc_GameEvent)

    @property
    def all_svc_user_message(self):
        """
        Returns list of (peek, message) for 'user message.'

        """
        return self.find_all_kind(pb_n.svc_UserMessage)
